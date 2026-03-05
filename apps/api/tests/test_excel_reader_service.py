from pathlib import Path

import pandas as pd

from app.services.excel_reader import read_excel_columns, read_excel_records


def test_read_excel_records_and_columns(tmp_path: Path):
    file_path = tmp_path / "datos.xlsx"
    df = pd.DataFrame(
        [
            {"NumeroProceso": "1", "NombreContribuyente": "ACME"},
            {"NumeroProceso": "2", "NombreContribuyente": "BETA"},
        ]
    )
    df.to_excel(file_path, index=False)

    records = read_excel_records(str(file_path))
    columns = read_excel_columns(str(file_path))

    assert len(records) == 2
    assert records[0]["NumeroProceso"] == "1"
    assert records[1]["NombreContribuyente"] == "BETA"
    assert columns == {"NumeroProceso", "NombreContribuyente"}
