import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._analysis import load_owned_analysis
from app.db.session import get_db
from app.models import LearningResource, User
from app.schemas.jobs import (
    JobSummaryRead,
    LearningResourceRead,
    SkillGapItemRead,
    SkillGapRead,
)
from app.services.matching import (
    compute_skill_gaps,
    get_embedder,
    match_profile,
)

router = APIRouter()


@router.get("/gap/{analysis_id}", response_model=SkillGapRead)
def get_skill_gap(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillGapRead:
    analysis = load_owned_analysis(db, current_user, analysis_id)
    profile = analysis.cv.profile

    pairs = match_profile(db, profile, get_embedder())
    results = [result for _, result in pairs]
    gaps = compute_skill_gaps(results, top_jobs=10)

    resources_by_skill: dict[uuid.UUID, list[LearningResourceRead]] = {}
    skill_ids = [gap.skill_id for gap in gaps]
    if skill_ids:
        resources = db.scalars(
            select(LearningResource)
            .where(LearningResource.skill_id.in_(skill_ids))
            .order_by(LearningResource.title)
        )
        for resource in resources:
            resources_by_skill.setdefault(resource.skill_id, []).append(
                LearningResourceRead(
                    title=resource.title, url=resource.url
                )
            )

    top_jobs = [
        JobSummaryRead(
            job_id=job.id,
            slug=job.slug,
            title=job.title,
            company=job.company,
            level=job.level,
            match_percentage=round(result.match_score * 100, 1),
        )
        for job, result in pairs[:10]
    ]

    return SkillGapRead(
        analysis_id=analysis.id,
        top_jobs=top_jobs,
        gaps=[
            SkillGapItemRead(
                skill=gap.skill,
                category=gap.category,
                frequency=gap.frequency,
                job_count=gap.job_count,
                resources=resources_by_skill.get(gap.skill_id, []),
            )
            for gap in gaps
        ],
    )
