from pathlib import Path
from app.core.settings import settings

def batch_root(batch_id: str) -> Path:
    root = Path(settings.storage_root) / "batches" / batch_id
    root.mkdir(parents=True, exist_ok=True)
    for p in ["input", "docx", "pdf"]:
        (root / p).mkdir(parents=True, exist_ok=True)
    return root
