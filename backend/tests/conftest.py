import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "llm_api_key", "")
    monkeypatch.setattr(settings, "bcrypt_rounds", 4)
    monkeypatch.setattr(settings, "rate_limit_per_minute", 1000)
    limiter.reset()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    limiter.reset()


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def user_payload():
    return {"email": "user@example.com", "password": "rahasia123"}


@pytest.fixture
def auth_token(client, user_payload):
    client.post("/auth/register", json=user_payload)
    response = client.post("/auth/login", json=user_payload)
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def auth_headers_factory(client):
    def factory(email: str) -> dict[str, str]:
        payload = {"email": email, "password": "rahasia123"}
        client.post("/auth/register", json=payload)
        token = client.post("/auth/login", json=payload).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture
def fixture_path():
    def resolve(name: str):
        return FIXTURES_DIR / name

    return resolve


PDF_MIME = "application/pdf"
DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


@pytest.fixture
def upload_file(client):
    def upload(headers, filename: str, content_type: str | None = None):
        path = FIXTURES_DIR / filename
        mime = content_type
        if mime is None:
            mime = PDF_MIME if path.suffix == ".pdf" else DOCX_MIME
        return client.post(
            "/cv/upload",
            headers=headers,
            files={"file": (filename, path.read_bytes(), mime)},
        )

    return upload
