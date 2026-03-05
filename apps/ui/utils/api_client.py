import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def create_batch(excel_bytes: bytes, excel_name: str, template_bytes: bytes, template_name: str, filename_pattern: str):
    files = {
        "excel": (excel_name, excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "template": (template_name, template_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    data = {"filename_pattern": filename_pattern}
    r = requests.post(f"{API_BASE_URL}/batches", files=files, data=data, timeout=120)
    r.raise_for_status()
    return r.json()["batch_id"]

def run_batch(batch_id: str):
    r = requests.post(f"{API_BASE_URL}/batches/{batch_id}/run", timeout=60)
    r.raise_for_status()
    return r.json()

def get_status(batch_id: str):
    r = requests.get(f"{API_BASE_URL}/batches/{batch_id}", timeout=30)
    r.raise_for_status()
    return r.json()

def download_zip(batch_id: str) -> bytes:
    r = requests.get(f"{API_BASE_URL}/batches/{batch_id}/download", timeout=300)
    r.raise_for_status()
    return r.content

def download_errors(batch_id: str) -> bytes:
    r = requests.get(f"{API_BASE_URL}/batches/{batch_id}/errors", timeout=60)
    r.raise_for_status()
    return r.content
