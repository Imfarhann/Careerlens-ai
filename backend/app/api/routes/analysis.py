import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.routes._analysis import load_owned_analysis
from app.db.session import get_db
from app.models import Analysis, CV, Profile, User, UserSkill
from app.schemas.analysis import AnalysisRead
from app.schemas.dashboard import (
    AnalysisCompareRead,
    AnalysisHistoryItemRead,
    AnalysisHistoryRead,
    CriterionComparisonRead,
)
from app.services.llm import generate_suggestions
from app.services.scoring import ScoringInput, score_cv

router = APIRouter()


def _load_cv(db: Session, user: User, cv_id: uuid.UUID) -> CV:
    cv = db.scalar(
        select(CV)
        .where(CV.id == cv_id, CV.user_id == user.id)
        .options(
            selectinload(CV.profile)
            .selectinload(Profile.user_skills)
            .selectinload(UserSkill.skill)
        )
    )
    if cv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV tidak ditemukan",
        )
    return cv


def _build_scoring_input(cv: CV) -> ScoringInput:
    profile = cv.profile
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil CV tidak ditemukan",
        )

    return ScoringInput(
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        summary=profile.summary,
        links=profile.links or {},
        education=profile.education or [],
        experience=profile.experience or [],
        projects=profile.projects or [],
        skills=[
            {"name": skill.name, "category": skill.category}
            for skill in profile.skills
        ],
        raw_text=cv.raw_text or "",
        page_count=cv.page_count,
        has_tables=bool(cv.has_tables),
        has_images=bool(cv.has_images),
    )


@router.post(
    "/{cv_id}",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis(
    cv_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Analysis:
    cv = _load_cv(db, current_user, cv_id)
    data = _build_scoring_input(cv)
    result = score_cv(data)
    suggestions = generate_suggestions(data, result)

    analysis = Analysis(
        cv_id=cv.id,
        total_score=result.total_score,
        score_breakdown={"version": 1, **result.to_dict()},
        suggestions=suggestions,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@router.get("", response_model=AnalysisHistoryRead)
def list_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisHistoryRead:
    rows = db.execute(
        select(Analysis, CV.original_filename)
        .join(CV, CV.id == Analysis.cv_id)
        .where(CV.user_id == current_user.id)
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
    ).all()
    return AnalysisHistoryRead(
        analyses=[
            AnalysisHistoryItemRead(
                id=analysis.id,
                cv_id=analysis.cv_id,
                original_filename=filename,
                created_at=analysis.created_at,
                total_score=analysis.total_score,
            )
            for analysis, filename in rows
        ]
    )


def _criteria_map(analysis: Analysis) -> dict[str, dict]:
    return {
        item["key"]: item
        for item in (analysis.score_breakdown or {}).get("criteria", [])
    }


@router.get(
    "/{analysis_id}/compare/{other_id}",
    response_model=AnalysisCompareRead,
)
def compare_analyses(
    analysis_id: uuid.UUID,
    other_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisCompareRead:
    base = load_owned_analysis(db, current_user, analysis_id)
    other = load_owned_analysis(db, current_user, other_id)

    base_criteria = _criteria_map(base)
    other_criteria = _criteria_map(other)
    ordered_keys = list(base_criteria)
    ordered_keys.extend(
        key for key in other_criteria if key not in base_criteria
    )

    criteria: list[CriterionComparisonRead] = []
    for key in ordered_keys:
        base_item = base_criteria.get(key, {})
        other_item = other_criteria.get(key, {})
        base_score = int(base_item.get("score", 0))
        compare_score = int(other_item.get("score", 0))
        criteria.append(
            CriterionComparisonRead(
                key=key,
                label=base_item.get("label")
                or other_item.get("label")
                or key,
                base_score=base_score,
                compare_score=compare_score,
                delta=compare_score - base_score,
                max_score=int(
                    base_item.get("max_score")
                    or other_item.get("max_score")
                    or 0
                ),
            )
        )

    base_skills = {
        skill.name for skill in base.cv.profile.skills if skill.name
    }
    other_skills = {
        skill.name for skill in other.cv.profile.skills if skill.name
    }

    return AnalysisCompareRead(
        base_analysis_id=base.id,
        compare_analysis_id=other.id,
        base_total_score=base.total_score,
        compare_total_score=other.total_score,
        total_score_delta=other.total_score - base.total_score,
        criteria=criteria,
        skills_added=sorted(
            other_skills - base_skills, key=str.casefold
        ),
        skills_removed=sorted(
            base_skills - other_skills, key=str.casefold
        ),
    )


@router.get("/{analysis_id}", response_model=AnalysisRead)
def get_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Analysis:
    analysis = db.scalar(
        select(Analysis)
        .join(CV, CV.id == Analysis.cv_id)
        .where(Analysis.id == analysis_id, CV.user_id == current_user.id)
    )
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analisis tidak ditemukan",
        )
    return analysis
