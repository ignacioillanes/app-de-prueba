"""CLI principal del analizador de mercado de postgrados chilenos."""
import sys
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@click.group()
def cli():
    """Analizador del mercado de postgrados y educación continua en Chile."""
    pass


@cli.command()
@click.option("--fuente", "-f", multiple=True,
              type=click.Choice(["uc", "uchile", "usach", "uai", "cned", "todas"]),
              default=["todas"], show_default=True,
              help="Fuente(s) a scrapear.")
@click.option("--verbose", "-v", is_flag=True)
def scrape(fuente, verbose):
    """Extrae programas de postgrado desde universidades y fuentes públicas."""
    from .scrapers.uc import UCScraper
    from .scrapers.uchile import UChileScraper
    from .scrapers.usach import USACHScraper
    from .scrapers.uai import UAIScraper
    from .scrapers.cned import CNEDClient
    from .utils.storage import save_raw

    scrapers_map = {
        "uc": (UCScraper, "scrape"),
        "uchile": (UChileScraper, "scrape"),
        "usach": (USACHScraper, "scrape"),
        "uai": (UAIScraper, "scrape"),
        "cned": (CNEDClient, "fetch"),
    }
    fuentes_sel = list(scrapers_map.keys()) if "todas" in fuente else list(fuente)

    total_guardados = 0
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        for nombre in fuentes_sel:
            cls, metodo = scrapers_map[nombre]
            task = progress.add_task(f"Scrapeando [bold]{nombre}[/bold]...", total=None)
            try:
                inst = cls()
                programas = getattr(inst, metodo)()
                if hasattr(inst, "close"):
                    inst.close()
                path = save_raw(programas, nombre)
                progress.update(task, description=f"[green]{nombre}[/green]: {len(programas)} programas → {path.name}")
                total_guardados += len(programas)
                if verbose:
                    for p in programas[:3]:
                        console.print(f"  - {p.nombre} ({p.tipo})")
            except Exception as e:
                progress.update(task, description=f"[red]{nombre}: Error - {e}[/red]")
            progress.stop_task(task)

    console.print(f"\n[bold green]Listo.[/bold green] {total_guardados} programas guardados en data/raw/")


@cli.command()
def analizar():
    """Muestra análisis completo del mercado en consola."""
    from .utils.storage import load_all
    from .analysis.reportes import mostrar_resumen, mostrar_instituciones, mostrar_precios, mostrar_modalidades

    df = load_all()
    if df.empty:
        console.print("[red]Sin datos. Ejecuta primero:[/red] python -m src.cli scrape")
        sys.exit(1)
    n_fuentes = df["fuente"].nunique() if "fuente" in df.columns else "?"
    console.print(f"\n[dim]Datos cargados: {len(df)} programas de {n_fuentes} fuentes[/dim]\n")
    mostrar_resumen(df)
    console.print()
    mostrar_instituciones(df)
    console.print()
    mostrar_precios(df)
    console.print()
    mostrar_modalidades(df)


@cli.command()
@click.option("--formato", type=click.Choice(["csv", "excel", "markdown"]),
              default="markdown", show_default=True)
def exportar(formato):
    """Exporta los datos procesados a CSV, Excel o Markdown."""
    from .utils.storage import load_all, save_processed, export_excel
    from .analysis.reportes import exportar_markdown

    df = load_all()
    if df.empty:
        console.print("[red]Sin datos. Ejecuta primero: python -m src.cli scrape[/red]")
        sys.exit(1)

    if formato == "csv":
        path = save_processed(df)
    elif formato == "excel":
        path = export_excel(df)
    else:
        path = exportar_markdown(df)

    console.print(f"[green]Exportado:[/green] {path}")


@cli.command()
@click.argument("csv_path", type=click.Path(exists=True))
def ingestar(csv_path):
    """
    Ingesta un CSV de programas al directorio data/manual/.

    El CSV debe tener columnas: institucion, nombre, tipo, area, modalidad.
    Columnas opcionales: arancel_clp, duracion_meses, ciudad, region, url.
    """
    import shutil
    from pathlib import Path
    from .utils.storage import MANUAL_DIR
    import pandas as pd

    df = pd.read_csv(csv_path)
    required = {"institucion", "nombre", "tipo", "area", "modalidad"}
    missing = required - set(df.columns)
    if missing:
        console.print(f"[red]Faltan columnas requeridas: {missing}[/red]")
        sys.exit(1)

    dest = MANUAL_DIR / "programas.csv"
    if dest.exists():
        existing = pd.read_csv(dest)
        df = pd.concat([existing, df], ignore_index=True).drop_duplicates(
            subset=["institucion", "nombre", "tipo"]
        )
    df.to_csv(dest, index=False)
    console.print(f"[green]{len(df)} programas guardados en {dest}[/green]")


@cli.command()
@click.option("--tipo", default=None, help="Filtrar por tipo (magister, doctorado, diplomado...)")
@click.option("--modalidad", default=None, help="Filtrar por modalidad (online, presencial, hibrido)")
@click.option("--area", default=None, help="Filtrar por área")
@click.option("--institucion", default=None, help="Filtrar por institución")
@click.option("--max-precio", type=int, default=None, help="Precio máximo en CLP")
def buscar(tipo, modalidad, area, institucion, max_precio):
    """Busca programas con filtros específicos."""
    from .utils.storage import load_all
    from rich.table import Table
    from rich import box

    df = load_all()
    if df.empty:
        console.print("[red]Sin datos.[/red]")
        sys.exit(1)

    if tipo:
        df = df[df["tipo"].str.contains(tipo, case=False, na=False)]
    if modalidad:
        df = df[df["modalidad"].str.contains(modalidad, case=False, na=False)]
    if area:
        df = df[df["area"].str.contains(area, case=False, na=False)]
    if institucion:
        df = df[df["institucion"].str.contains(institucion, case=False, na=False)]
    if max_precio:
        df = df[(df["arancel_clp"].isna()) | (df["arancel_clp"] <= max_precio)]

    console.print(f"\n[bold]{len(df)} programas encontrados[/bold]\n")
    if df.empty:
        return

    t = Table(box=box.ROUNDED)
    cols = ["nombre", "institucion", "tipo", "area", "modalidad", "arancel_clp"]
    cols_exist = [c for c in cols if c in df.columns]
    for c in cols_exist:
        t.add_column(c.capitalize())
    for _, row in df.head(50).iterrows():
        vals = []
        for c in cols_exist:
            v = row[c]
            if c == "arancel_clp" and pd.notna(v):
                v = f"${int(v):,}"
            vals.append(str(v) if pd.notna(v) else "-")
        t.add_row(*vals)
    console.print(t)


if __name__ == "__main__":
    cli()
