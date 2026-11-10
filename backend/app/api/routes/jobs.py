import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._analysis import load_owned_analysis
from app.db.session import get_db
from app.models import Job, User
from app.schemas.jobs import JobMatchesRead, JobMatchRead
from app.services.matching import (
    MatchResult,
    get_embedder,
    match_profile,
    upsert_job_matches,
)

router = APIRouter()


def _required_and_optional(job: Job) -> tuple[list[str], list[str]]:
    required: set[str] = set()
    optional: set[str] = set()
    for item in job.skills:
        if item.skill is None:
            continue
        if item.is_required:
            required.add(item.skill.name)
        else:
            optional.add(item.skill.name)
    optional -= required
    return sorted(required), sorted(optional)


def _match_read(job: Job, result: MatchResult) -> JobMatchRead:
    required, optional = _required_and_optional(job)
    return JobMatchRead(
        job_id=job.id,
        slug=job.slug,
        title=job.title,
        company=job.company,
        level=job.level,
        description=job.description,
        match_score=result.match_score,
        match_percentage=round(result.match_score * 100, 1),
        skill_coverage=result.skill_coverage,
        semantic_similarity=result.semantic_similarity,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        required_skills=required,
        nice_to_have_skills=optional,
    )


@router.get("/match/{analysis_id}", response_model=JobMatchesRead)
def get_job_matches(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobMatchesRead:
    analysis = load_owned_analysis(db, current_user, analysis_id)
    profile = analysis.cv.profile

    pairs = match_profile(db, profile, get_embedder())
    matches = [_match_read(job, result) for job, result in pairs]

    upsert_job_matches(
        db, analysis.id, [result for _, result in pairs]
    )

    return JobMatchesRead(analysis_id=analysis.id, matches=matches)
