import pandas as pd
import pytest
from src.analysis.tendencias import (
    resumen_general, oferta_por_institucion, analisis_precios, tendencia_modalidad
)


@pytest.fixture
def df_sample():
    return pd.DataFrame([
        {"institucion": "UC", "nombre": "MBA", "tipo": "magister", "area": "negocios",
         "modalidad": "presencial", "arancel_clp": 10_000_000, "fuente": "manual"},
        {"institucion": "UChile", "nombre": "Doctorado Química", "tipo": "doctorado",
         "area": "ciencias", "modalidad": "presencial", "arancel_clp": None, "fuente": "manual"},
        {"institucion": "UAI", "nombre": "Diplomado Marketing", "tipo": "diplomado",
         "area": "negocios", "modalidad": "online", "arancel_clp": 1_200_000, "fuente": "manual"},
        {"institucion": "UC", "nombre": "Magíster Derecho", "tipo": "magister",
         "area": "derecho", "modalidad": "presencial", "arancel_clp": 8_000_000, "fuente": "manual"},
    ])


def test_resumen_general(df_sample):
    r = resumen_general(df_sample)
    assert r["total_programas"] == 4
    assert r["instituciones"] == 3
    assert r["tipos"]["magister"] == 2


def test_oferta_por_institucion(df_sample):
    t = oferta_por_institucion(df_sample)
    assert t.iloc[0]["institucion"] == "UC"
    assert t.iloc[0]["total"] == 2


def test_analisis_precios(df_sample):
    p = analisis_precios(df_sample)
    assert not p.empty
    magister = p[p["tipo"] == "magister"].iloc[0]
    assert magister["promedio_clp"] == 9_000_000


def test_tendencia_modalidad(df_sample):
    t = tendencia_modalidad(df_sample)
    assert "modalidad" in t.columns
    assert len(t) > 0
