from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update

from app.models import Analysis, Job, JobSkill, LearningResource
from app.services.matching import set_embedder
from app.services.profile_store import resolve_skill


class FixedEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


@pytest.fixture
def fake_embedder():
    embedder = FixedEmbedder()
    set_embedder(embedder)
    try:
        yield embedder
    finally:
        set_embedder(None)


def add_job(db, slug, title, required, nice=()):
    job = Job(
        slug=slug,
        title=title,
        company="Contoh",
        level="Junior",
        description=f"Lowongan {title} untuk pengujian dashboard.",
    )
    db.add(job)
    db.flush()
    for name in required:
        skill = resolve_skill(db, name)
        db.add(
            JobSkill(
                job_id=job.id, skill_id=skill.id, is_required=True
            )
        )
    for name in nice:
        skill = resolve_skill(db, name)
        db.add(
            JobSkill(
                job_id=job.id, skill_id=skill.id, is_required=False
            )
        )
    return job


@pytest.fixture
def manual_jobs(db_session):
    add_job(
        db_session,
        "job-a",
        "Backend A",
        required=["Python", "React"],
        nice=["PostgreSQL"],
    )
    add_job(
        db_session,
        "job-b",
        "Backend B",
        required=["Python", "PostgreSQL"],
        nice=["Communication"],
    )
    postgres = resolve_skill(db_session, "PostgreSQL")
    db_session.add(
        LearningResource(
            skill_id=postgres.id,
            title="PostgreSQL Tutorial",
            url="https://www.postgresql.org/docs/current/tutorial.html",
        )
    )
    db_session.commit()
    return db_session


def make_analysis(client, headers, upload_file, skills):
    upload = upload_file(headers, "indonesian.pdf").json()
    response = client.put(
        f"/profile/{upload['profile']['id']}",
        headers=headers,
        json={"skills": [{"name": name} for name in skills]},
    )
    assert response.status_code == 200

    response = client.post(
        f"/analysis/{upload['cv']['id']}", headers=headers
    )
    assert response.status_code == 201
    return response.json()


def test_dashboard_category_coverage_and_top_gaps(
    client,
    auth_headers,
    upload_file,
    fake_embedder,
    manual_jobs,
):
    analysis = make_analysis(
        client, auth_headers, upload_file, ["Python", "React", "Communication"]
    )

    response = client.get(
        f"/dashboard/{analysis['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == analysis["id"]
    assert body["total_score"] == analysis["total_score"]
    assert body["score_breakdown"] == analysis["score_breakdown"]

    counts = {
        item["category"]: item["count"]
        for item in body["skill_by_category"]
    }
    assert counts == {
        "Programming": 1,
        "Web": 1,
        "Soft Skill": 1,
    }

    coverage = {
        item["category"]: item
        for item in body["category_coverage"]
    }
    assert coverage["Programming"] == {
        "category": "Programming",
        "owned": 1,
        "total": 1,
        "percentage": 100.0,
    }
    assert coverage["Web"] == {
        "category": "Web",
        "owned": 1,
        "total": 1,
        "percentage": 100.0,
    }
    assert coverage["Database"] == {
        "category": "Database",
        "owned": 0,
        "total": 1,
        "percentage": 0.0,
    }
    assert "Soft Skill" not in coverage

    assert len(body["top_matches"]) == 2
    assert body["top_matches"][0]["title"] == "Backend A"
    assert body["top_matches"][0]["match_percentage"] == pytest.approx(
        88.0
    )
    assert body["top_matches"][1]["match_percentage"] == pytest.approx(
        76.0
    )

    gaps = body["top_gaps"]
    assert [item["skill"] for item in gaps] == ["PostgreSQL"]
    assert gaps[0]["frequency"] == 2
    assert gaps[0]["job_count"] == 1
    assert gaps[0]["resources"][0]["title"] == "PostgreSQL Tutorial"


def test_dashboard_without_skills_has_zero_coverage(
    client,
    auth_headers,
    upload_file,
    fake_embedder,
    manual_jobs,
):
    analysis = make_analysis(
        client, auth_headers, upload_file, []
    )

    response = client.get(
        f"/dashboard/{analysis['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["skill_by_category"] == []
    assert all(
        item["owned"] == 0 and item["percentage"] == 0.0
        for item in body["category_coverage"]
    )
    assert {item["category"] for item in body["category_coverage"]} == {
        "Programming",
        "Web",
        "Database",
    }

    gap_skills = [item["skill"] for item in body["top_gaps"]]
    assert gap_skills[:2] == ["Python", "PostgreSQL"]
    assert "React" in gap_skills
    assert "Communication" in gap_skills


def test_analysis_history_is_newest_first(
    client, auth_headers, upload_file, fake_embedder, manual_jobs, db_session
):
    first = make_analysis(
        client, auth_headers, upload_file, ["Python"]
    )
    old_time = datetime.now(timezone.utc) - timedelta(days=2)
    db_session.execute(
        update(Analysis)
        .where(Analysis.id == UUID(first["id"]))
        .values(created_at=old_time)
    )
    db_session.commit()

    second = make_analysis(
        client, auth_headers, upload_file, ["Python", "React"]
    )

    response = client.get("/analysis", headers=auth_headers)

    assert response.status_code == 200
    analyses = response.json()["analyses"]
    assert [item["id"] for item in analyses] == [
        second["id"],
        first["id"],
    ]
    assert analyses[0]["cv_id"] == second["cv_id"]
    assert analyses[0]["original_filename"]
    assert analyses[0]["total_score"] == second["total_score"]
    assert analyses[0]["created_at"]


def test_compare_analysis_scores_and_skills(
    client, auth_headers, upload_file, fake_embedder, manual_jobs
):
    base = make_analysis(
        client, auth_headers, upload_file, ["Python", "React"]
    )
    compare = make_analysis(
        client, auth_headers, upload_file, ["Python", "PostgreSQL"]
    )

    response = client.get(
        f"/analysis/{base['id']}/compare/{compare['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["base_analysis_id"] == base["id"]
    assert body["compare_analysis_id"] == compare["id"]
    assert body["base_total_score"] == base["total_score"]
    assert body["compare_total_score"] == compare["total_score"]
    assert body["total_score_delta"] == (
        compare["total_score"] - base["total_score"]
    )
    assert body["skills_added"] == ["PostgreSQL"]
    assert body["skills_removed"] == ["React"]

    assert len(body["criteria"]) == 5
    assert sum(item["max_score"] for item in body["criteria"]) == 100
    for item in body["criteria"]:
        assert item["delta"] == item["compare_score"] - item["base_score"]


def test_empty_history_and_unknown_dashboard(
    client, auth_headers, fake_embedder, manual_jobs
):
    history = client.get("/analysis", headers=auth_headers)
    assert history.status_code == 200
    assert history.json()["analyses"] == []

    assert (
        client.get(
            f"/dashboard/{uuid4()}", headers=auth_headers
        ).status_code
        == 404
    )


def test_dashboard_and_compare_enforce_ownership(
    client,
    auth_headers,
    auth_headers_factory,
    upload_file,
    fake_embedder,
    manual_jobs,
):
    analysis = make_analysis(
        client, auth_headers, upload_file, ["Python"]
    )
    other_headers = auth_headers_factory("other@example.com")
    other_analysis = make_analysis(
        client, other_headers, upload_file, ["Python"]
    )

    assert (
        client.get(
            f"/dashboard/{analysis['id']}", headers=other_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/analysis/{analysis['id']}/compare/{analysis['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/analysis/{analysis['id']}/compare/{other_analysis['id']}",
            headers=auth_headers,
        ).status_code
        == 404
    )
    assert (
        client.get("/analysis", headers=other_headers).json()["analyses"][0][
            "id"
        ]
        == other_analysis["id"]
    )


def test_dashboard_requires_authentication(
    client, fake_embedder, manual_jobs
):
    assert client.get(f"/dashboard/{uuid4()}").status_code == 401
