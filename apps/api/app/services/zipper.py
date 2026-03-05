from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def zip_pdfs(pdf_dir: str, zip_path: str) -> None:
    pdf_dir_p = Path(pdf_dir)
    zip_path_p = Path(zip_path)
    zip_path_p.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path_p, "w", compression=ZIP_DEFLATED) as z:
        for f in sorted(pdf_dir_p.glob("*.pdf")):
            z.write(f, arcname=f.name)
