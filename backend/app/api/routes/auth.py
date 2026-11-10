from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Analysis, CV, JobMatch, Profile, User, UserSkill
from app.schemas.auth import LoginRequest, Token, UserCreate, UserRead

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("auth:register"))],
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    email = payload.email.strip().lower()

    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit("auth:login"))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    cv_rows = db.execute(
        select(CV.id, CV.file_path).where(CV.user_id == current_user.id)
    ).all()
    cv_ids = [row[0] for row in cv_rows]
    file_paths = [row[1] for row in cv_rows]

    if cv_ids:
        analysis_ids = db.scalars(
            select(Analysis.id).where(Analysis.cv_id.in_(cv_ids))
        ).all()
        profile_ids = db.scalars(
            select(Profile.id).where(Profile.cv_id.in_(cv_ids))
        ).all()

        if analysis_ids:
            db.execute(
                delete(JobMatch).where(JobMatch.analysis_id.in_(analysis_ids))
            )
            db.execute(
                delete(Analysis).where(Analysis.id.in_(analysis_ids))
            )
        if profile_ids:
            db.execute(
                delete(UserSkill).where(UserSkill.profile_id.in_(profile_ids))
            )
            db.execute(delete(Profile).where(Profile.id.in_(profile_ids)))
        db.execute(delete(CV).where(CV.id.in_(cv_ids)))

    db.delete(current_user)
    db.commit()

    upload_root = Path(settings.upload_dir).resolve()
    for raw_path in file_paths:
        try:
            resolved = Path(raw_path).resolve()
            if resolved.is_relative_to(upload_root):
                resolved.unlink(missing_ok=True)
        except OSError:
            pass

    return Response(status_code=status.HTTP_204_NO_CONTENT)
