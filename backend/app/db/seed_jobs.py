import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobSkill, LearningResource
from app.services.profile_store import resolve_skill

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
JOBS_FILE = DATA_DIR / "jobs_seed.json"
RESOURCES_FILE = DATA_DIR / "learning_resources.json"


def load_jobs(path: Path | None = None) -> list[dict[str, Any]]:
    with (path or JOBS_FILE).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_resources(path: Path | None = None) -> list[dict[str, Any]]:
    with (path or RESOURCES_FILE).open(encoding="utf-8") as handle:
        return json.load(handle)


def _sync_job_skills(
    db: Session, job: Job, entry: dict[str, Any]
) -> None:
    desired: dict[Any, bool] = {}
    for name in entry.get("required_skills", []):
        skill = resolve_skill(db, name)
        desired[skill.id] = True
    for name in entry.get("nice_to_have_skills", []):
        skill = resolve_skill(db, name)
        desired.setdefault(skill.id, False)

    existing = {
        item.skill_id: item
        for item in db.scalars(
            select(JobSkill).where(JobSkill.job_id == job.id)
        )
    }
    for skill_id, is_required in desired.items():
        current = existing.get(skill_id)
        if current is None:
            db.add(
                JobSkill(
                    job_id=job.id,
                    skill_id=skill_id,
                    is_required=is_required,
                )
            )
        else:
            current.is_required = is_required
    for skill_id, item in existing.items():
        if skill_id not in desired:
            db.delete(item)


def _sync_resources(
    db: Session, resources: list[dict[str, Any]]
) -> dict[str, int]:
    created = updated = 0
    for entry in resources:
        skill = resolve_skill(db, entry["skill"])
        resource = db.scalar(
            select(LearningResource).where(
                LearningResource.skill_id == skill.id,
                LearningResource.url == entry["url"],
            )
        )
        if resource is None:
            db.add(
                LearningResource(
                    skill_id=skill.id,
                    title=entry["title"],
                    url=entry["url"],
                )
            )
            created += 1
        elif resource.title != entry["title"]:
            resource.title = entry["title"]
            updated += 1
    return {"resources_created": created, "resources_updated": updated}


def seed(
    db: Session,
    jobs_data: list[dict[str, Any]] | None = None,
    resources_data: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    jobs_data = jobs_data if jobs_data is not None else load_jobs()
    resources_data = (
        resources_data if resources_data is not None else load_resources()
    )

    existing_jobs = {
        job.slug: job for job in db.scalars(select(Job))
    }
    created = updated = 0

    for entry in jobs_data:
        job = existing_jobs.get(entry["slug"])
        if job is None:
            job = Job(
                slug=entry["slug"],
                title=entry["title"],
                company=entry["company"],
                level=entry["level"],
                description=entry["description"],
            )
            db.add(job)
            existing_jobs[entry["slug"]] = job
            created += 1
        else:
            if job.description != entry["description"]:
                job.embedding = None
            job.title = entry["title"]
            job.company = entry["company"]
            job.level = entry["level"]
            job.description = entry["description"]
            updated += 1
        db.flush()
        _sync_job_skills(db, job, entry)

    result = _sync_resources(db, resources_data)
    db.commit()

    return {
        "jobs_created": created,
        "jobs_updated": updated,
        **result,
    }


def main() -> None:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        counts = seed(db)
    print(
        "Seed selesai: "
        f"{counts['jobs_created']} lowongan dibuat, "
        f"{counts['jobs_updated']} diperbarui, "
        f"{counts['resources_created']} sumber belajar dibuat, "
        f"{counts['resources_updated']} diperbarui."
    )


if __name__ == "__main__":
    main()
