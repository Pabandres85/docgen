from pathlib import Path
from zipfile import ZipFile

from app.services.zipper import zip_pdfs


def test_zip_pdfs_includes_only_pdf_files(tmp_path: Path):
    pdf_dir = tmp_path / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    (pdf_dir / "b.pdf").write_bytes(b"%PDF-1.4 b")
    (pdf_dir / "a.pdf").write_bytes(b"%PDF-1.4 a")
    (pdf_dir / "notes.txt").write_text("ignore")

    zip_path = tmp_path / "salida.zip"
    zip_pdfs(str(pdf_dir), str(zip_path))

    with ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
    assert names == ["a.pdf", "b.pdf"]
