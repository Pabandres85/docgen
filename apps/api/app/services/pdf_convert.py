import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.settings import settings


def docx_to_pdf_libreoffice(docx_path: str, out_dir: str, timeout_seconds: int | None = None) -> str:
    out_dir_p = Path(out_dir).resolve()
    docx_path_p = Path(docx_path).resolve()

    # Each conversion gets its own isolated LibreOffice user profile to avoid
    # profile lock conflicts when multiple workers run in parallel.
    lo_profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    try:
        cmd = [
            "soffice",
            f"-env:UserInstallation=file://{lo_profile}",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir_p),
            str(docx_path_p),
        ]
        timeout = timeout_seconds or settings.libreoffice_timeout_seconds
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"LibreOffice excedio el tiempo limite ({timeout}s)") from e

        if result.returncode != 0:
            detail = result.stderr.decode(errors="ignore")[:1000]
            raise RuntimeError(f"LibreOffice fallo: {detail}")

        pdf_path = out_dir_p / (docx_path_p.stem + ".pdf")
        if not pdf_path.exists():
            raise FileNotFoundError(f"No se genero PDF: {pdf_path}")
        return str(pdf_path)
    finally:
        shutil.rmtree(lo_profile, ignore_errors=True)
