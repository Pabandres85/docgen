import pandas as pd

def read_excel_records(excel_path: str) -> list[dict]:
    df = pd.read_excel(excel_path, dtype=str).fillna("")
    return df.to_dict(orient="records")
