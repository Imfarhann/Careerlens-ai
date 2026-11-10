import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import CV, Profile, User, UserSkill
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.profile_store import replace_profile_skills

router = APIRouter()


def _load_profile(
    db: Session, user: User, profile_id: uuid.UUID
) -> Profile:
    profile = db.scalar(
        select(Profile)
        .join(CV, CV.id == Profile.cv_id)
        .where(Profile.id == profile_id, CV.user_id == user.id)
        .options(
            selectinload(Profile.cv),
            selectinload(Profile.user_skills).selectinload(UserSkill.skill),
        )
        .execution_options(populate_existing=True)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil tidak ditemukan",
        )
    return profile


@router.get("/{profile_id}", response_model=ProfileRead)
def get_profile(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Profile:
    return _load_profile(db, current_user, profile_id)


@router.put("/{profile_id}", response_model=ProfileRead)
def update_profile(
    profile_id: uuid.UUID,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Profile:
    profile = _load_profile(db, current_user, profile_id)
    data = payload.model_dump(exclude_unset=True)
    skills = data.pop("skills", None)

    for field, value in data.items():
        if field == "links" and value is None:
            value = {"github": None, "linkedin": None, "other": []}
        setattr(profile, field, value)

    if skills is not None:
        replace_profile_skills(db, profile, skills)

    db.commit()
    return _load_profile(db, current_user, profile_id)
