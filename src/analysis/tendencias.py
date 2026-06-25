"""Análisis de tendencias del mercado de postgrados y educación continua chilena."""
import pandas as pd
from typing import Optional


def resumen_general(df: pd.DataFrame) -> dict:
    return {
        "total_programas": len(df),
        "instituciones": df["institucion"].nunique(),
        "tipos": df["tipo"].value_counts().to_dict(),
        "modalidades": df["modalidad"].value_counts().to_dict(),
        "areas": df["area"].value_counts().to_dict(),
    }


def oferta_por_institucion(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("institucion")
        .agg(
            total=("nombre", "count"),
            magisteres=("tipo", lambda s: (s == "magister").sum()),
            doctorados=("tipo", lambda s: (s == "doctorado").sum()),
            diplomados=("tipo", lambda s: (s == "diplomado").sum()),
            cursos=("tipo", lambda s: (s == "curso").sum()),
        )
        .sort_values("total", ascending=False)
        .reset_index()
    )


def oferta_por_area(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["area", "tipo"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .sort_values(df["tipo"].value_counts().index[0] if len(df) else "area", ascending=False)
    )


def analisis_precios(df: pd.DataFrame) -> pd.DataFrame:
    precios = df[df["arancel_clp"].notna() & (df["arancel_clp"] > 0)].copy()
    if precios.empty:
        return pd.DataFrame(columns=["tipo", "promedio_clp", "minimo_clp", "maximo_clp", "mediana_clp", "n"])
    return (
        precios.groupby("tipo")["arancel_clp"]
        .agg(
            promedio_clp="mean",
            minimo_clp="min",
            maximo_clp="max",
            mediana_clp="median",
            n="count",
        )
        .reset_index()
        .assign(
            promedio_clp=lambda x: x["promedio_clp"].round(0).astype(int),
            mediana_clp=lambda x: x["mediana_clp"].round(0).astype(int),
        )
    )


def tendencia_modalidad(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["modalidad", "tipo"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )


def ranking_programas_online(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    online = df[df["modalidad"].isin(["online", "hibrido"])].copy()
    cols = ["nombre", "institucion", "tipo", "area", "arancel_clp", "modalidad", "url"]
    cols_exist = [c for c in cols if c in online.columns]
    return online[cols_exist].head(top_n)


def brechas_precio_modalidad(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    precios = df[df["arancel_clp"].notna() & (df["arancel_clp"] > 0)]
    if precios.empty or "modalidad" not in precios.columns:
        return None
    return (
        precios.groupby("modalidad")["arancel_clp"]
        .agg(promedio="mean", mediana="median", n="count")
        .reset_index()
        .assign(
            promedio=lambda x: x["promedio"].round(0).astype(int),
            mediana=lambda x: x["mediana"].round(0).astype(int),
        )
    )
