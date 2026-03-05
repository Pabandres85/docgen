import csv
import shutil
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Batch, BatchItem
from app.db.session import SessionLocal
from app.services.excel_reader import read_excel_records
from app.services.naming import apply_pattern
from app.services.pdf_convert import docx_to_pdf_libreoffice
from app.services.storage import batch_root
from app.services.template_render import render_docx
from app.services.zipper import zip_pdfs
from app.workers.celery_app import celery_app


def _convert_with_retry(out_docx: Path, pdf_dir: Path, attempts: int = 2) -> Path:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            pdf_path = docx_to_pdf_libreoffice(str(out_docx), str(pdf_dir))
            return Path(pdf_path)
        except Exception as e:
            last_error = e
            if attempt < attempts:
                time.sleep(1)
    raise RuntimeError(f"Fallo conversion DOCX->PDF tras {attempts} intentos: {last_error}")


def _set_failed(batch: Batch, db: Session, message: str) -> None:
    batch.status = "FAILED"
    batch.error += 1
    db.commit()
    raise RuntimeError(message)


@celery_app.task(name="process_batch")
def process_batch(batch_id: str) -> dict:
    db: Session = SessionLocal()
    try:
        batch = db.get(Batch, batch_id)
        if not batch:
            return {"ok": False, "error": "Batch not found"}

        root = batch_root(batch_id)
        pdf_dir = root / "pdf"
        docx_dir = root / "docx"
        excel_path = root / batch.input_excel
        template_path = root / batch.input_template

        if not excel_path.exists():
            _set_failed(batch, db, f"Excel no encontrado: {excel_path}")
        if not template_path.exists():
            _set_failed(batch, db, f"Plantilla no encontrada: {template_path}")

        batch.status = "RUNNING"
        batch.total = 0
        batch.ok = 0
        batch.error = 0
        db.query(BatchItem).filter(BatchItem.batch_id == batch_id).delete()
        db.commit()

        try:
            records = read_excel_records(str(excel_path))
        except Exception as e:
            _set_failed(batch, db, f"Error leyendo Excel: {e}")

        batch.total = len(records)
        db.commit()

        ok = 0
        err = 0
        errors = []

        for idx, row in enumerate(records, start=1):
            item = BatchItem(batch_id=batch_id, row_index=idx, status="PENDING")
            db.add(item)
            db.commit()

            try:
                base_name = apply_pattern(batch.filename_pattern, row, idx)
                out_docx = docx_dir / f"{base_name}.docx"

                try:
                    render_docx(str(template_path), row, str(out_docx))
                except Exception as e:
                    raise RuntimeError(f"Error renderizando DOCX: {e}") from e

                generated_pdf = _convert_with_retry(out_docx, pdf_dir, attempts=2)
                final_pdf = pdf_dir / f"{base_name}.pdf"
                if generated_pdf != final_pdf:
                    shutil.move(str(generated_pdf), str(final_pdf))

                item.status = "OK"
                item.output_pdf = f"batches/{batch_id}/pdf/{final_pdf.name}"
                ok += 1

            except Exception as e:
                item.status = "ERROR"
                item.error_message = str(e)
                errors.append({"row": idx, "error": str(e)})
                err += 1

            db.commit()
            batch.ok = ok
            batch.error = err
            db.commit()

        errors_csv = root / "errores.csv"
        if errors:
            with open(errors_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["row", "error"])
                writer.writeheader()
                writer.writerows(errors)
            batch.errors_csv = f"batches/{batch_id}/errores.csv"
        else:
            errors_csv.unlink(missing_ok=True)
            batch.errors_csv = ""

        try:
            zip_path = root / "salida.zip"
            zip_pdfs(str(pdf_dir), str(zip_path))
            batch.output_zip = f"batches/{batch_id}/salida.zip"
        except Exception as e:
            _set_failed(batch, db, f"Error generando ZIP: {e}")

        batch.status = "DONE" if err == 0 else "DONE_WITH_ERRORS"
        db.commit()
        return {
            "ok": True,
            "batch_id": batch_id,
            "total": batch.total,
            "ok_count": ok,
            "error_count": err,
            "status": batch.status,
        }

    except Exception as e:
        batch = db.get(Batch, batch_id)
        if batch:
            batch.status = "FAILED"
            db.commit()
        return {"ok": False, "batch_id": batch_id, "error": str(e)}
    finally:
        db.close()
