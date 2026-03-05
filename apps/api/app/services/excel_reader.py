import pandas as pd

def read_excel_records(excel_path: str) -> list[dict]:
    df = pd.read_excel(excel_path, dtype=str).fillna("")
    return df.to_dict(orient="records")


def read_excel_columns(excel_path: str) -> set[str]:
    df = pd.read_excel(excel_path, dtype=str, nrows=0)
    return {str(c) for c in df.columns}
