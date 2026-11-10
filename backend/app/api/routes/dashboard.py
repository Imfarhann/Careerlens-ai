import uuid
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes._analysis import load_owned_analysis
from app.db.session import get_db
from app.models import LearningResource, User
from app.schemas.dashboard import (
    CategoryCoverageRead,
    DashboardMatchRead,
    DashboardRead,
    SkillCategoryCountRead,
)
from app.schemas.jobs import LearningResourceRead, SkillGapItemRead
from app.services.matching import (
    compute_skill_gaps,
    get_embedder,
    match_profile,
)
from app.services.skills_catalog import category_rank

router = APIRouter()

TOP_JOBS = 10


def _sort_categories(categories: set[str]) -> list[str]:
    return sorted(categories, key=lambda name: (category_rank(name), name))


@router.get("/{analysis_id}", response_model=DashboardRead)
def get_dashboard(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardRead:
    analysis = load_owned_analysis(db, current_user, analysis_id)
    profile = analysis.cv.profile

    pairs = match_profile(db, profile, get_embedder())
    results = [result for _, result in pairs]
    top_pairs = pairs[:TOP_JOBS]

    profile_skills = [
        skill for skill in profile.skills if skill is not None
    ]
    owned_ids = {skill.id for skill in profile_skills}

    counts = Counter(
        skill.category or "Other" for skill in profile_skills
    )
    skill_by_category = [
        SkillCategoryCountRead(category=category, count=counts[category])
        for category in _sort_categories(set(counts))
    ]

    needed_by_category: dict[str, set[uuid.UUID]] = {}
    for job, _ in top_pairs:
        for item in job.skills:
            if item.skill is None or not item.is_required:
                continue
            category = item.skill.category or "Other"
            needed_by_category.setdefault(category, set()).add(
                item.skill_id
            )

    category_coverage = []
    for category in _sort_categories(set(needed_by_category)):
        needed = needed_by_category[category]
        owned = len(needed & owned_ids)
        total = len(needed)
        category_coverage.append(
            CategoryCoverageRead(
                category=category,
                owned=owned,
                total=total,
                percentage=round(owned / total * 100, 1) if total else 0.0,
            )
        )

    top_matches = [
        DashboardMatchRead(
            job_id=job.id,
            slug=job.slug,
            title=job.title,
            company=job.company,
            level=job.level,
            match_percentage=round(result.match_score * 100, 1),
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
        )
        for job, result in pairs[:5]
    ]

    gaps = compute_skill_gaps(results, top_jobs=TOP_JOBS)[:5]
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

    top_gaps = [
        SkillGapItemRead(
            skill=gap.skill,
            category=gap.category,
            frequency=gap.frequency,
            job_count=gap.job_count,
            resources=resources_by_skill.get(gap.skill_id, []),
        )
        for gap in gaps
    ]

    suggestions = analysis.suggestions or {
        "items": [],
        "source": "fallback",
    }

    return DashboardRead(
        analysis_id=analysis.id,
        created_at=analysis.created_at,
        total_score=analysis.total_score,
        score_breakdown=analysis.score_breakdown,
        skill_by_category=skill_by_category,
        category_coverage=category_coverage,
        top_matches=top_matches,
        top_gaps=top_gaps,
        suggestions=suggestions,
    )
