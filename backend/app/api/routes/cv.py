import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import CV, Profile, User
from app.schemas.cv import CVRead, UploadResult
from app.schemas.profile import ProfileRead
from app.services.nlp import extract_profile
from app.services.parser import (
    DOCX_MIME,
    PDF_MIME,
    EmptyDocumentError,
    ParserError,
    is_docx_bytes,
    is_pdf_bytes,
    parse_document_detailed,
)
from app.services.profile_store import add_profile_skills

router = APIRouter()

EXTENSION_MIME = {".pdf": PDF_MIME, ".docx": DOCX_MIME}
ACCEPTED_CONTENT_TYPES = {PDF_MIME, DOCX_MIME, "application/octet-stream"}


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            limit_mb = limit // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Ukuran file melebihi batas {limit_mb} MB.",
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _validate_file_meta(file: UploadFile) -> tuple[str, str]:
    original = file.filename or ""
    suffix = Path(original).suffix.lower()

    if suffix not in EXTENSION_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format file harus PDF atau DOCX.",
        )

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ACCEPTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipe konten file tidak didukung. Unggah file PDF atau DOCX.",
        )

    expected = EXTENSION_MIME[suffix]
    if content_type not in {expected, "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipe konten file tidak sesuai dengan ekstensinya.",
        )

    return Path(original).name[:255], suffix


def _validate_magic(data: bytes, suffix: str) -> None:
    if suffix == ".pdf" and not is_pdf_bytes(data):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Isi file tidak cocok dengan format PDF.",
        )
    if suffix == ".docx" and not is_docx_bytes(data):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Isi file tidak cocok dengan format DOCX.",
        )


@router.post(
    "/upload",
    response_model=UploadResult,
    status_code=status.HTTP_201_CREATED,
)
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResult:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File tidak ditemukan pada permintaan.",
        )

    original_filename, suffix = _validate_file_meta(file)
    data = await _read_limited(file, settings.max_upload_size)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File kosong. Unggah CV yang berisi teks.",
        )

    _validate_magic(data, suffix)

    try:
        parsed = parse_document_detailed(data, suffix)
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    text = parsed.text
    extracted = extract_profile(text)

    upload_root = Path(settings.upload_dir).resolve()
    upload_root.mkdir(parents=True, exist_ok=True)
    stored_path = upload_root / f"{uuid.uuid4().hex}{suffix}"
    stored_path.write_bytes(data)

    try:
        cv = CV(
            user_id=current_user.id,
            original_filename=original_filename,
            file_path=str(stored_path),
            raw_text=text,
            page_count=parsed.page_count,
            has_tables=parsed.has_tables,
            has_images=parsed.has_images,
        )
        profile = Profile(
            cv=cv,
            name=extracted["name"],
            email=extracted["email"],
            phone=extracted["phone"],
            summary=extracted["summary"],
            links=extracted["links"],
            education=extracted["education"],
            experience=extracted["experience"],
            projects=extracted["projects"],
            extra=extracted["extra"],
        )
        db.add(cv)
        db.flush()
        add_profile_skills(db, profile, extracted["skills"])
        db.commit()
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise

    db.refresh(profile)
    return UploadResult(
        cv=CVRead.model_validate(cv),
        profile=ProfileRead.model_validate(profile),
    )


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(
    cv_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    cv = db.scalar(
        select(CV).where(CV.id == cv_id, CV.user_id == current_user.id)
    )
    if cv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV tidak ditemukan",
        )

    stored_path = Path(cv.file_path)
    db.delete(cv)
    db.commit()

    upload_root = Path(settings.upload_dir).resolve()
    try:
        resolved = stored_path.resolve()
        if resolved.is_relative_to(upload_root):
            resolved.unlink(missing_ok=True)
    except OSError:
        pass

    return Response(status_code=status.HTTP_204_NO_CONTENT)
