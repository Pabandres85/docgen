import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ApiClientError(RuntimeError):
    pass


def _request(method: str, path: str, *, timeout: int, **kwargs):
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except requests.HTTPError as e:
        detail = ""
        try:
            body = response.json()
            detail = body.get("detail", "")
        except Exception:
            detail = response.text[:300]
        raise ApiClientError(f"Error API {response.status_code}: {detail}") from e
    except requests.RequestException as e:
        raise ApiClientError(f"No fue posible conectar con la API: {e}") from e


def create_batch(excel_bytes: bytes, excel_name: str, template_bytes: bytes, template_name: str, filename_pattern: str):
    files = {
        "excel": (excel_name, excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "template": (template_name, template_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }
    data = {"filename_pattern": filename_pattern}
    response = _request("POST", "/batches", files=files, data=data, timeout=120)
    return response.json()["batch_id"]


def run_batch(batch_id: str, force: bool = False):
    suffix = "?force=true" if force else ""
    response = _request("POST", f"/batches/{batch_id}/run{suffix}", timeout=60)
    return response.json()


def get_status(batch_id: str):
    response = _request("GET", f"/batches/{batch_id}", timeout=30)
    return response.json()


def download_zip(batch_id: str) -> bytes:
    response = _request("GET", f"/batches/{batch_id}/download", timeout=300)
    return response.content


def download_errors(batch_id: str) -> bytes:
    response = _request("GET", f"/batches/{batch_id}/errors", timeout=60)
    return response.content
