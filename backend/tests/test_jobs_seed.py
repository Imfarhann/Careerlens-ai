import re
from copy import deepcopy

from sqlalchemy import func, select

from app.db.seed_jobs import load_jobs, load_resources, seed
from app.models import Job, JobSkill, LearningResource
from app.services.skills_catalog import load_skills


def test_jobs_seed_has_forty_realistic_jobs():
    jobs = load_jobs()

    assert len(jobs) == 40
    assert len({job["slug"] for job in jobs}) == 40

    for job in jobs:
        assert job["title"].strip()
        assert job["company"].strip()
        assert job["level"] in {"Intern", "Junior", "Mid"}
        assert job["required_skills"]
        assert not set(job["required_skills"]) & set(
            job["nice_to_have_skills"]
        )

        sentences = [
            part
            for part in re.split(
                r"(?<=[.!?])\s+", job["description"].strip()
            )
            if part.strip()
        ]
        assert 3 <= len(sentences) <= 5, job["slug"]


def test_every_job_skill_exists_in_catalog():
    catalog = {item["name"] for item in load_skills()}
    jobs = load_jobs()

    used = set()
    for job in jobs:
        used.update(job["required_skills"])
        used.update(job["nice_to_have_skills"])

    assert used <= catalog, sorted(used - catalog)


def test_every_job_skill_has_learning_resource():
    jobs = load_jobs()
    resources = load_resources()

    used = set()
    for job in jobs:
        used.update(job["required_skills"])
        used.update(job["nice_to_have_skills"])

    covered = {entry["skill"] for entry in resources}
    assert used <= covered, sorted(used - covered)
    assert all(entry["title"].strip() for entry in resources)
    assert all(entry["url"].startswith("http") for entry in resources)


def test_seed_is_idempotent(db_session):
    first = seed(db_session)
    assert first["jobs_created"] == 40
    assert first["resources_created"] > 0

    job_count = db_session.scalar(select(func.count()).select_from(Job))
    job_skill_count = db_session.scalar(
        select(func.count()).select_from(JobSkill)
    )
    resource_count = db_session.scalar(
        select(func.count()).select_from(LearningResource)
    )
    assert job_count == 40

    second = seed(db_session)

    assert second["jobs_created"] == 0
    assert second["resources_created"] == 0
    assert (
        db_session.scalar(select(func.count()).select_from(Job))
        == job_count
    )
    assert (
        db_session.scalar(select(func.count()).select_from(JobSkill))
        == job_skill_count
    )
    assert (
        db_session.scalar(
            select(func.count()).select_from(LearningResource)
        )
        == resource_count
    )


def test_seed_resets_embedding_when_description_changes(db_session):
    data = deepcopy(load_jobs())
    seed(db_session, data)

    job = db_session.scalar(
        select(Job).where(Job.slug == data[0]["slug"])
    )
    job.embedding = [0.1, 0.2, 0.3]
    db_session.commit()

    data[0]["description"] = (
        "Deskripsi baru untuk pengujian. Kalimat kedua. Kalimat ketiga."
    )
    seed(db_session, data)
    db_session.refresh(job)

    assert job.description == data[0]["description"]
    assert job.embedding is None
