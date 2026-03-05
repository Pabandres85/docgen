import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

TEST_STORAGE = Path(tempfile.mkdtemp(prefix="docgen_test_storage_"))
os.environ.setdefault("STORAGE_ROOT", str(TEST_STORAGE))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_STORAGE / 'docgen_test.sqlite'}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/9")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:8501")

from app.db.session import Base, engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def cleanup_storage():
    yield
    shutil.rmtree(TEST_STORAGE, ignore_errors=True)
