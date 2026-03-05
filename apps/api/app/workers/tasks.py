import csv
import shutil
from pathlib import Path
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal, engine
from app.db.models import Batch, BatchItem
from app.services.storage import batch_root
from app.services.excel_reader import read_excel_records
from app.services.template_render import render_docx
from app.services.pdf_convert import docx_to_pdf_libreoffice
from app.services.naming import apply_pattern

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

        batch.status = "RUNNING"
        db.commit()

        records = read_excel_records(str(root / batch.input_excel))
        batch.total = len(records)
        db.query(BatchItem).filter(BatchItem.batch_id == batch_id).delete()
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
                render_docx(str(root / batch.input_template), row, str(out_docx))

                pdf_path = docx_to_pdf_libreoffice(str(out_docx), str(pdf_dir))
                final_pdf = pdf_dir / f"{base_name}.pdf"
                if Path(pdf_path) != final_pdf:
                    shutil.move(pdf_path, final_pdf)

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

        # errors.csv
        errors_csv = root / "errores.csv"
        if errors:
            with open(errors_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["row", "error"])
                w.writeheader()
                w.writerows(errors)
            batch.errors_csv = f"batches/{batch_id}/errores.csv"
        else:
            if errors_csv.exists():
                errors_csv.unlink(missing_ok=True)
            batch.errors_csv = ""

        # salida.zip
        zip_path = root / "salida.zip"
        from app.services.zipper import zip_pdfs
        zip_pdfs(str(pdf_dir), str(zip_path))
        batch.output_zip = f"batches/{batch_id}/salida.zip"

        batch.status = "DONE" if err == 0 else "DONE"
        db.commit()

        return {"ok": True, "batch_id": batch_id, "total": batch.total, "ok_count": ok, "error_count": err}

    finally:
        db.close()
