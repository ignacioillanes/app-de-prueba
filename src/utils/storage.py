import json
import csv
import pandas as pd
from pathlib import Path
from typing import List
from .models import Programa

RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
MANUAL_DIR = Path(__file__).parent.parent.parent / "data" / "manual"

for d in (RAW_DIR, PROCESSED_DIR, MANUAL_DIR):
    d.mkdir(parents=True, exist_ok=True)


def save_raw(programas: List[Programa], fuente: str) -> Path:
    path = RAW_DIR / f"{fuente}.json"
    existing = []
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
    data = existing + [p.to_dict() for p in programas]
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_all() -> pd.DataFrame:
    frames = []
    for path in RAW_DIR.glob("*.json"):
        with open(path) as f:
            data = json.load(f)
        if data:
            frames.append(pd.DataFrame(data))
    manual_csv = MANUAL_DIR / "programas.csv"
    if manual_csv.exists():
        frames.append(pd.read_csv(manual_csv))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df.drop_duplicates(subset=["institucion", "nombre", "tipo"], inplace=True)
    return df


def save_processed(df: pd.DataFrame, nombre: str = "consolidado") -> Path:
    path = PROCESSED_DIR / f"{nombre}.csv"
    df.to_csv(path, index=False)
    return path


def export_excel(df: pd.DataFrame, nombre: str = "reporte") -> Path:
    path = PROCESSED_DIR / f"{nombre}.xlsx"
    df.to_excel(path, index=False)
    return path
