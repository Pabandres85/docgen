import re
import unicodedata

import pandas as pd


def _normalize_col(col: str) -> str:
    """Convierte nombre de columna a identificador válido para Jinja2 y Python format.
    Ej: 'EXPEDIENTE DE COBRO' -> 'EXPEDIENTE_DE_COBRO'
        'RESOLUCIÓN MEDIDA PREVIA' -> 'RESOLUCION_MEDIDA_PREVIA'
    """
    nfkd = unicodedata.normalize("NFKD", str(col))
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9_]", "_", ascii_str)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "col"


def read_excel_records(excel_path: str) -> list[dict]:
    df = pd.read_excel(excel_path, dtype=str).fillna("")
    df.columns = [_normalize_col(c) for c in df.columns]
    return df.to_dict(orient="records")


def read_excel_columns(excel_path: str) -> set[str]:
    df = pd.read_excel(excel_path, dtype=str, nrows=0)
    return {_normalize_col(str(c)) for c in df.columns}
