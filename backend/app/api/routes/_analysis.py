import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Analysis, CV, Profile, User, UserSkill


def load_owned_analysis(
    db: Session, user: User, analysis_id: uuid.UUID
) -> Analysis:
    analysis = db.scalar(
        select(Analysis)
        .join(CV, CV.id == Analysis.cv_id)
        .where(Analysis.id == analysis_id, CV.user_id == user.id)
        .options(
            selectinload(Analysis.cv)
            .selectinload(CV.profile)
            .selectinload(Profile.user_skills)
            .selectinload(UserSkill.skill)
        )
    )
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analisis tidak ditemukan",
        )
    if analysis.cv is None or analysis.cv.profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil CV tidak ditemukan",
        )
    return analysis
