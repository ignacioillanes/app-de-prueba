"""Generación de reportes en consola y archivos."""
from pathlib import Path
from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from . import tendencias as T

console = Console()
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def mostrar_resumen(df: pd.DataFrame):
    if df.empty:
        console.print("[red]Sin datos para analizar. Ejecuta primero: python -m src.cli scrape[/red]")
        return

    resumen = T.resumen_general(df)
    console.print(Panel.fit(
        f"[bold cyan]Mercado de Postgrados Chile[/bold cyan]\n"
        f"Total programas: [green]{resumen['total_programas']}[/green]  |  "
        f"Instituciones: [green]{resumen['instituciones']}[/green]",
        title="Resumen General",
    ))

    _tabla_dict("Programas por Tipo", resumen["tipos"], ["Tipo", "Cantidad"])
    _tabla_dict("Programas por Modalidad", resumen["modalidades"], ["Modalidad", "Cantidad"])
    _tabla_dict("Top Áreas", dict(list(resumen["areas"].items())[:10]), ["Área", "Cantidad"])


def mostrar_instituciones(df: pd.DataFrame):
    tabla_df = T.oferta_por_institucion(df)
    t = Table(title="Oferta por Institución", box=box.ROUNDED)
    for col in tabla_df.columns:
        t.add_column(col.capitalize(), justify="right" if col != "institucion" else "left")
    for _, row in tabla_df.iterrows():
        t.add_row(*[str(v) for v in row])
    console.print(t)


def mostrar_precios(df: pd.DataFrame):
    precios = T.analisis_precios(df)
    if precios.empty:
        console.print("[yellow]No hay datos de precios disponibles.[/yellow]")
        return
    t = Table(title="Análisis de Precios por Tipo (CLP)", box=box.ROUNDED)
    cols = {"tipo": "Tipo", "promedio_clp": "Promedio", "mediana_clp": "Mediana",
            "minimo_clp": "Mínimo", "maximo_clp": "Máximo", "n": "N"}
    for col, label in cols.items():
        if col in precios.columns:
            t.add_column(label, justify="right" if col != "tipo" else "left")
    for _, row in precios.iterrows():
        vals = []
        for col in cols:
            if col in precios.columns:
                v = row[col]
                vals.append(f"${v:,.0f}" if "clp" in col else str(v))
        t.add_row(*vals)
    console.print(t)

    brechas = T.brechas_precio_modalidad(df)
    if brechas is not None:
        console.print()
        t2 = Table(title="Precio Promedio por Modalidad (CLP)", box=box.ROUNDED)
        for col in ["modalidad", "promedio", "mediana", "n"]:
            t2.add_column(col.capitalize(), justify="right" if col != "modalidad" else "left")
        for _, row in brechas.iterrows():
            t2.add_row(
                str(row["modalidad"]),
                f"${row['promedio']:,}",
                f"${row['mediana']:,}",
                str(row["n"]),
            )
        console.print(t2)


def mostrar_modalidades(df: pd.DataFrame):
    modal = T.tendencia_modalidad(df)
    t = Table(title="Distribución por Modalidad y Tipo", box=box.ROUNDED)
    for col in modal.columns:
        t.add_column(str(col).capitalize(), justify="right" if col != "modalidad" else "left")
    for _, row in modal.iterrows():
        t.add_row(*[str(v) for v in row])
    console.print(t)

    console.print()
    online = T.ranking_programas_online(df)
    if not online.empty:
        t2 = Table(title="Programas Online / Híbridos", box=box.ROUNDED)
        for col in online.columns:
            t2.add_column(col.capitalize())
        for _, row in online.iterrows():
            t2.add_row(*[str(v) for v in row])
        console.print(t2)


def exportar_markdown(df: pd.DataFrame) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"reporte_{ts}.md"
    lines = [
        "# Reporte Mercado Postgrados Chile",
        f"_Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}_\n",
    ]
    resumen = T.resumen_general(df)
    lines += [
        "## Resumen General",
        f"- **Total programas:** {resumen['total_programas']}",
        f"- **Instituciones:** {resumen['instituciones']}",
        "",
        "## Distribución por Tipo",
        _md_tabla(pd.DataFrame(resumen["tipos"].items(), columns=["Tipo", "Cantidad"])),
        "",
        "## Distribución por Modalidad",
        _md_tabla(pd.DataFrame(resumen["modalidades"].items(), columns=["Modalidad", "Cantidad"])),
        "",
        "## Precios por Tipo",
        _md_tabla(T.analisis_precios(df)),
        "",
        "## Oferta por Institución",
        _md_tabla(T.oferta_por_institucion(df).head(20)),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _md_tabla(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin datos_"
    return df.to_markdown(index=False)


def _tabla_dict(titulo: str, data: dict, cols: list):
    t = Table(title=titulo, box=box.SIMPLE)
    for c in cols:
        t.add_column(c)
    for k, v in data.items():
        t.add_row(str(k), str(v))
    console.print(t)
