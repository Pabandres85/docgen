from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import Batch
from app.db.session import get_db
from app.schemas.batches import BatchCreateResponse, BatchRunResponse, BatchStatusResponse
from app.services.excel_reader import read_excel_columns
from app.services.naming import extract_pattern_fields
from app.services.storage import batch_root, sanitize_upload_filename
from app.workers.tasks import process_batch

router = APIRouter(prefix="/batches", tags=["batches"])


def _validate_upload(filename: str, expected_ext: str, size_bytes: int) -> None:
    if not filename.lower().endswith(expected_ext):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Archivo invalido: se esperaba extension {expected_ext}",
        )
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande. Limite: {settings.max_upload_mb} MB",
        )


def _validate_pattern_columns(batch: Batch, batch_id: str) -> None:
    root = batch_root(batch_id)
    excel_abs = root / batch.input_excel
    try:
        excel_cols = read_excel_columns(str(excel_abs))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo leer el Excel para validar columnas: {e}",
        ) from e
    required_fields = extract_pattern_fields(batch.filename_pattern) - {"row_index"}
    missing = sorted([field for field in required_fields if field not in excel_cols])
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "El patron de nombre requiere columnas no presentes en el Excel",
                "missing_columns": missing,
            },
        )


@router.post("", response_model=BatchCreateResponse)
async def create_batch(
    excel: UploadFile = File(...),
    template: UploadFile = File(...),
    filename_pattern: str = Form("registro_{row_index}"),
    db: Session = Depends(get_db),
):
    excel_name = sanitize_upload_filename(excel.filename or "", "datos.xlsx")
    template_name = sanitize_upload_filename(template.filename or "", "plantilla.docx")

    excel_bytes = await excel.read()
    template_bytes = await template.read()

    _validate_upload(excel_name, ".xlsx", len(excel_bytes))
    _validate_upload(template_name, ".docx", len(template_bytes))

    batch = Batch(filename_pattern=filename_pattern.strip() or "registro_{row_index}")
    db.add(batch)
    db.commit()
    db.refresh(batch)

    root = batch_root(batch.id)
    excel_path = root / "input" / excel_name
    template_path = root / "input" / template_name

    excel_path.write_bytes(excel_bytes)
    template_path.write_bytes(template_bytes)

    batch.input_excel = f"input/{excel_name}"
    batch.input_template = f"input/{template_name}"
    db.commit()

    return BatchCreateResponse(batch_id=batch.id)


@router.post("/{batch_id}/run", response_model=BatchRunResponse)
def run_batch(batch_id: str, force: bool = Query(False), db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    non_rerunnable_statuses = {"RUNNING", "DONE", "DONE_WITH_ERRORS"}
    if batch.status in non_rerunnable_statuses and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Batch en estado {batch.status}. Usa force=true para relanzarlo.",
        )

    _validate_pattern_columns(batch, batch_id)

    process_batch.delay(batch_id)
    batch.status = "RUNNING"
    db.commit()
    return BatchRunResponse(batch_id=batch_id, status=batch.status)


@router.get("/{batch_id}", response_model=BatchStatusResponse)
def get_status(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    progress = 0.0
    if batch.total > 0:
        progress = round((batch.ok + batch.error) / batch.total, 4)
    return BatchStatusResponse(
        batch_id=batch.id,
        status=batch.status,
        total=batch.total,
        ok=batch.ok,
        error=batch.error,
        progress=progress,
    )


@router.get("/{batch_id}/download")
def download_zip(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch or not batch.output_zip:
        raise HTTPException(status_code=404, detail="ZIP not available")
    root = batch_root(batch_id)
    file_path = root / Path(batch.output_zip).name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ZIP not found on disk")
    return FileResponse(str(file_path), media_type="application/zip", filename="salida.zip")


@router.get("/{batch_id}/errors")
def download_errors(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch or not batch.errors_csv:
        raise HTTPException(status_code=404, detail="No errors file")
    root = batch_root(batch_id)
    file_path = root / Path(batch.errors_csv).name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Errors file not found on disk")
    return FileResponse(str(file_path), media_type="text/csv", filename="errores.csv")
