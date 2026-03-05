from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil

from app.db.session import get_db, engine, Base
from app.db.models import Batch
from app.schemas.batches import BatchCreateResponse, BatchStatusResponse, BatchRunResponse
from app.services.storage import batch_root
from app.workers.tasks import process_batch

router = APIRouter(prefix="/batches", tags=["batches"])

@router.post("", response_model=BatchCreateResponse)
async def create_batch(
    excel: UploadFile = File(...),
    template: UploadFile = File(...),
    filename_pattern: str = Form("registro_{row_index}"),
    db: Session = Depends(get_db),
):
    batch = Batch(filename_pattern=filename_pattern)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    root = batch_root(batch.id)

    excel_path = root / "input" / excel.filename
    template_path = root / "input" / template.filename

    with open(excel_path, "wb") as f:
        shutil.copyfileobj(excel.file, f)
    with open(template_path, "wb") as f:
        shutil.copyfileobj(template.file, f)

    batch.input_excel = f"input/{excel.filename}"
    batch.input_template = f"input/{template.filename}"
    db.commit()

    return BatchCreateResponse(batch_id=batch.id)

@router.post("/{batch_id}/run", response_model=BatchRunResponse)
def run_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status in ("RUNNING",):
        return BatchRunResponse(batch_id=batch_id, status=batch.status)

    # dispatch async
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
        progress=progress
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
