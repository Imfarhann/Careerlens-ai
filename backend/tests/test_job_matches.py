from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.db.seed_jobs import seed
from app.models import Job, JobMatch
from app.services.matching import set_embedder


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


@pytest.fixture
def seeded_jobs(db_session):
    seed(db_session)
    return db_session


def make_analysis(client, headers, upload_file, skills=None):
    upload = upload_file(headers, "indonesian.pdf").json()
    if skills is not None:
        response = client.put(
            f"/profile/{upload['profile']['id']}",
            headers=headers,
            json={"skills": skills},
        )
        assert response.status_code == 200

    response = client.post(
        f"/analysis/{upload['cv']['id']}", headers=headers
    )
    assert response.status_code == 201
    return response.json()


def test_job_matches_are_sorted_and_expose_score_components(
    client, auth_headers, upload_file, fake_embedder, seeded_jobs
):
    analysis = make_analysis(client, auth_headers, upload_file)

    response = client.get(
        f"/jobs/match/{analysis['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == analysis["id"]
    matches = body["matches"]
    assert len(matches) == 40

    scores = [item["match_score"] for item in matches]
    assert scores == sorted(scores, reverse=True)

    for item in matches:
        assert 0.0 <= item["skill_coverage"] <= 1.0
        assert 0.0 <= item["semantic_similarity"] <= 1.0
        expected = 0.6 * item["skill_coverage"] + 0.4 * item[
            "semantic_similarity"
        ]
        assert item["match_score"] == pytest.approx(expected, abs=1e-5)
        assert item["match_percentage"] == pytest.approx(
            round(item["match_score"] * 100, 1)
        )

        allowed = set(item["required_skills"]) | set(
            item["nice_to_have_skills"]
        )
        assert set(item["matched_skills"]) <= allowed
        assert set(item["missing_skills"]) <= allowed
        assert not set(item["matched_skills"]) & set(
            item["missing_skills"]
        )
        assert item["semantic_similarity"] == pytest.approx(1.0)


def test_job_matches_are_persisted_without_duplicates(
    client, auth_headers, upload_file, fake_embedder, seeded_jobs
):
    analysis = make_analysis(client, auth_headers, upload_file)

    first = client.get(
        f"/jobs/match/{analysis['id']}", headers=auth_headers
    )
    second = client.get(
        f"/jobs/match/{analysis['id']}", headers=auth_headers
    )
    assert first.status_code == second.status_code == 200

    seeded_jobs.rollback()
    count = seeded_jobs.scalar(
        select(func.count())
        .select_from(JobMatch)
        .where(JobMatch.analysis_id == UUID(analysis["id"]))
    )
    assert count == 40


def test_skill_gap_returns_prioritized_missing_skills(
    client, auth_headers, upload_file, fake_embedder, seeded_jobs
):
    analysis = make_analysis(client, auth_headers, upload_file)

    response = client.get(
        f"/skills/gap/{analysis['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == analysis["id"]
    assert len(body["top_jobs"]) == 10

    percentages = [
        item["match_percentage"] for item in body["top_jobs"]
    ]
    assert percentages == sorted(percentages, reverse=True)

    gaps = body["gaps"]
    assert gaps
    frequencies = [item["frequency"] for item in gaps]
    assert frequencies == sorted(frequencies, reverse=True)
    for item in gaps:
        assert item["skill"]
        assert item["category"]
        assert item["frequency"] >= 1
        assert item["job_count"] <= item["frequency"]
        assert item["resources"]
        assert all(
            resource["url"].startswith("http")
            for resource in item["resources"]
        )


def test_profile_without_skills_has_zero_coverage(
    client, auth_headers, upload_file, fake_embedder, seeded_jobs
):
    analysis = make_analysis(
        client, auth_headers, upload_file, skills=[]
    )

    response = client.get(
        f"/jobs/match/{analysis['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    matches = response.json()["matches"]
    assert matches
    for item in matches:
        assert item["skill_coverage"] == 0.0
        assert item["matched_skills"] == []
        assert item["missing_skills"]
        assert item["match_score"] == pytest.approx(
            0.4 * item["semantic_similarity"]
        )

    gap = client.get(
        f"/skills/gap/{analysis['id']}", headers=auth_headers
    ).json()
    assert gap["gaps"]
    assert sum(item["frequency"] for item in gap["gaps"]) > 0


def test_job_without_skills_has_full_coverage(
    client, auth_headers, upload_file, fake_embedder, seeded_jobs
):
    job = Job(
        slug="no-skill-test",
        title="Generalist Intern",
        company="Contoh",
        level="Intern",
        description="Lowongan umum untuk pemula. Tidak ada skill khusus.",
    )
    seeded_jobs.add(job)
    seeded_jobs.commit()

    analysis = make_analysis(client, auth_headers, upload_file)
    response = client.get(
        f"/jobs/match/{analysis['id']}", headers=auth_headers
    )

    match = next(
        item
        for item in response.json()["matches"]
        if item["slug"] == "no-skill-test"
    )
    assert match["skill_coverage"] == 1.0
    assert match["missing_skills"] == []
    assert match["match_score"] == pytest.approx(1.0)


def test_job_endpoints_enforce_ownership(
    client,
    auth_headers,
    auth_headers_factory,
    upload_file,
    fake_embedder,
    seeded_jobs,
):
    analysis = make_analysis(client, auth_headers, upload_file)
    other_headers = auth_headers_factory("other@example.com")

    assert (
        client.get(
            f"/jobs/match/{analysis['id']}", headers=other_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/skills/gap/{analysis['id']}", headers=other_headers
        ).status_code
        == 404
    )


def test_job_endpoints_require_authentication(
    client, auth_headers, upload_file, fake_embedder, seeded_jobs
):
    analysis = make_analysis(client, auth_headers, upload_file)

    assert (
        client.get(f"/jobs/match/{analysis['id']}").status_code == 401
    )
    assert (
        client.get(f"/skills/gap/{analysis['id']}").status_code == 401
    )


def test_unknown_analysis_returns_404(
    client, auth_headers, fake_embedder, seeded_jobs
):
    unknown = uuid4()

    assert (
        client.get(
            f"/jobs/match/{unknown}", headers=auth_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/skills/gap/{unknown}", headers=auth_headers
        ).status_code
        == 404
    )
