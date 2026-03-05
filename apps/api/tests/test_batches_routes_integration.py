from io import BytesIO

import pandas as pd

from app.db.models import Batch
from app.db.session import SessionLocal


def _excel_bytes(columns: list[str], rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows, columns=columns)
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def _create_batch(client, excel_name: str = "datos.xlsx", pattern: str = "Proceso_{NumeroProceso}") -> str:
    excel = _excel_bytes(
        columns=["NumeroProceso", "NombreContribuyente"],
        rows=[{"NumeroProceso": "100", "NombreContribuyente": "ACME"}],
    )
    files = {
        "excel": (excel_name, excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "template": ("plantilla.docx", b"fake-docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    data = {"filename_pattern": pattern}
    response = client.post("/batches", files=files, data=data)
    assert response.status_code == 200, response.text
    return response.json()["batch_id"]


def test_create_batch_rejects_wrong_excel_extension(client):
    files = {
        "excel": ("datos.txt", b"bad", "text/plain"),
        "template": ("plantilla.docx", b"fake-docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    response = client.post("/batches", files=files, data={"filename_pattern": "registro_{row_index}"})
    assert response.status_code == 422


def test_run_batch_enqueues_and_sets_running(client, monkeypatch):
    batch_id = _create_batch(client)
    called = []

    def _fake_delay(received_batch_id: str):
        called.append(received_batch_id)

    monkeypatch.setattr("app.routes.batches.process_batch.delay", _fake_delay)

    response = client.post(f"/batches/{batch_id}/run")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "RUNNING"
    assert called == [batch_id]


def test_run_batch_returns_conflict_when_already_done(client):
    batch_id = _create_batch(client)
    db = SessionLocal()
    try:
        batch = db.get(Batch, batch_id)
        batch.status = "DONE"
        db.commit()
    finally:
        db.close()

    response = client.post(f"/batches/{batch_id}/run")
    assert response.status_code == 409


def test_run_batch_validates_pattern_columns(client):
    batch_id = _create_batch(client, pattern="Proceso_{ColumnaInexistente}")
    response = client.post(f"/batches/{batch_id}/run")
    assert response.status_code == 422
    body = response.json()
    assert "missing_columns" in body["detail"]


def test_get_status_progress_uses_ok_plus_error(client):
    batch_id = _create_batch(client)
    db = SessionLocal()
    try:
        batch = db.get(Batch, batch_id)
        batch.total = 10
        batch.ok = 7
        batch.error = 1
        batch.status = "RUNNING"
        db.commit()
    finally:
        db.close()

    response = client.get(f"/batches/{batch_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["progress"] == 0.8
