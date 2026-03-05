import subprocess
from pathlib import Path

def docx_to_pdf_libreoffice(docx_path: str, out_dir: str) -> str:
    out_dir_p = Path(out_dir).resolve()
    docx_path_p = Path(docx_path).resolve()

    cmd = [
        "soffice",
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--convert-to", "pdf",
        "--outdir", str(out_dir_p),
        str(docx_path_p),
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice falló: {result.stderr.decode(errors='ignore')[:1000]}")

    pdf_path = out_dir_p / (docx_path_p.stem + ".pdf")
    if not pdf_path.exists():
        raise FileNotFoundError(f"No se generó PDF: {pdf_path}")
    return str(pdf_path)
