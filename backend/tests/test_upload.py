from pathlib import Path

from app.core.config import settings

PDF_MIME = "application/pdf"
DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def stored_files() -> list[Path]:
    root = Path(settings.upload_dir)
    return list(root.iterdir()) if root.exists() else []


def test_upload_pdf_creates_cv_and_profile(client, auth_headers, upload_file):
    response = upload_file(auth_headers, "indonesian.pdf")

    assert response.status_code == 201
    body = response.json()
    assert body["cv"]["original_filename"] == "indonesian.pdf"
    assert body["cv"]["id"]
    profile = body["profile"]
    assert profile["name"] == "RIZKY PRATAMA"
    assert profile["email"] == "rizky.pratama@example.com"
    assert profile["cv_id"] == body["cv"]["id"]
    assert {skill["name"] for skill in profile["skills"]} >= {
        "Python",
        "FastAPI",
        "Docker",
    }
    assert len(stored_files()) == 1


def test_upload_docx_creates_cv_and_profile(client, auth_headers, upload_file):
    response = upload_file(auth_headers, "english.docx")

    assert response.status_code == 201
    body = response.json()
    profile = body["profile"]
    assert profile["name"] == "ALEX MORGAN"
    assert "University of California" in profile["education"][0]["institution"]


def test_upload_requires_authentication(client, upload_file):
    response = upload_file({}, "indonesian.pdf")

    assert response.status_code == 401
    assert stored_files() == []


def test_upload_rejects_unsupported_extension(client, auth_headers):
    response = client.post(
        "/cv/upload",
        headers=auth_headers,
        files={"file": ("cv.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == 415
    assert "PDF atau DOCX" in response.json()["detail"]
    assert stored_files() == []


def test_upload_rejects_wrong_content_type(client, auth_headers, upload_file):
    response = upload_file(auth_headers, "indonesian.pdf", "text/plain")

    assert response.status_code == 415
    assert stored_files() == []


def test_upload_rejects_pdf_extension_with_fake_magic(client, auth_headers):
    response = client.post(
        "/cv/upload",
        headers=auth_headers,
        files={"file": ("cv.pdf", b"bukan pdf", PDF_MIME)},
    )

    assert response.status_code == 415
    assert "PDF" in response.json()["detail"]
    assert stored_files() == []


def test_upload_rejects_docx_extension_with_fake_magic(client, auth_headers):
    response = client.post(
        "/cv/upload",
        headers=auth_headers,
        files={"file": ("cv.docx", b"PK\x03\x04bukan zip", DOCX_MIME)},
    )

    assert response.status_code == 415
    assert "DOCX" in response.json()["detail"]
    assert stored_files() == []


def test_upload_rejects_oversized_file(client, auth_headers):
    oversized = b"%PDF-1.4\n" + b"0" * (5 * 1024 * 1024)

    response = client.post(
        "/cv/upload",
        headers=auth_headers,
        files={"file": ("big.pdf", oversized, PDF_MIME)},
    )

    assert response.status_code == 413
    assert "5 MB" in response.json()["detail"]
    assert stored_files() == []


def test_upload_rejects_empty_file(client, auth_headers):
    response = client.post(
        "/cv/upload",
        headers=auth_headers,
        files={"file": ("empty.pdf", b"", PDF_MIME)},
    )

    assert response.status_code == 400
    assert "kosong" in response.json()["detail"].lower()
    assert stored_files() == []


def test_upload_scanned_pdf_returns_friendly_error(client, auth_headers, upload_file):
    response = upload_file(auth_headers, "scanned.pdf")

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "scan" in detail.lower()
    assert "DOCX" in detail
    assert stored_files() == []


def test_upload_corrupt_pdf_returns_422(client, auth_headers):
    response = client.post(
        "/cv/upload",
        headers=auth_headers,
        files={"file": ("rusak.pdf", b"%PDF-1.4\nrusak", PDF_MIME)},
    )

    assert response.status_code == 422
    assert stored_files() == []


def test_delete_cv_removes_record_and_file(
    client, auth_headers, upload_file
):
    upload = upload_file(auth_headers, "indonesian.pdf").json()
    cv_id = upload["cv"]["id"]
    profile_id = upload["profile"]["id"]

    response = client.delete(f"/cv/{cv_id}", headers=auth_headers)

    assert response.status_code == 204
    assert stored_files() == []
    assert client.get(f"/profile/{profile_id}", headers=auth_headers).status_code == 404


def test_delete_cv_requires_ownership(
    client, auth_headers, auth_headers_factory, upload_file
):
    upload = upload_file(auth_headers, "indonesian.pdf").json()
    other_headers = auth_headers_factory("other@example.com")

    response = client.delete(f"/cv/{upload['cv']['id']}", headers=other_headers)

    assert response.status_code == 404
    assert len(stored_files()) == 1


def test_delete_unknown_cv_returns_404(client, auth_headers):
    from uuid import uuid4

    response = client.delete(f"/cv/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404
