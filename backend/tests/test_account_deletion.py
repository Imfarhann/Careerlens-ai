from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.models import (
    Analysis,
    CV,
    Job,
    JobMatch,
    Profile,
    User,
    UserSkill,
)
from app.services.matching import set_embedder


class FixedEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]


def test_delete_account_removes_all_data_and_files(
    client,
    auth_headers,
    auth_headers_factory,
    upload_file,
    db_session,
):
    set_embedder(FixedEmbedder())
    try:
        user = db_session.scalar(
            select(User).where(User.email == "user@example.com")
        )
        user_id = user.id

        uploaded = upload_file(auth_headers, "indonesian.pdf").json()
        cv_id = UUID(uploaded["cv"]["id"])
        profile_id = UUID(uploaded["profile"]["id"])
        cv = db_session.get(CV, cv_id)
        stored_path = Path(cv.file_path)
        assert stored_path.exists()

        analysis = client.post(
            f"/analysis/{cv_id}", headers=auth_headers
        ).json()
        analysis_id = UUID(analysis["id"])

        job = Job(
            slug="account-deletion-job",
            title="Backend Engineer",
            company="Contoh",
            level="Junior",
            description="Lowongan untuk pengujian hapus akun.",
        )
        db_session.add(job)
        db_session.flush()
        match = JobMatch(
            analysis_id=analysis_id,
            job_id=job.id,
            match_score=0.5,
            skill_coverage=0.5,
            semantic_similarity=0.5,
            matched_skills=[],
            missing_skills=[],
        )
        db_session.add(match)
        db_session.commit()
        match_id = match.id

        other_headers = auth_headers_factory("other@example.com")
        other_upload = upload_file(other_headers, "english.docx").json()
        other_cv_id = UUID(other_upload["cv"]["id"])

        response = client.delete("/auth/me", headers=auth_headers)

        assert response.status_code == 204

        db_session.expire_all()
        assert db_session.get(User, user_id) is None
        assert db_session.get(CV, cv_id) is None
        assert db_session.get(Profile, profile_id) is None
        assert db_session.get(Analysis, analysis_id) is None
        assert db_session.get(JobMatch, match_id) is None
        assert (
            db_session.scalar(
                select(UserSkill).where(UserSkill.profile_id == profile_id)
            )
            is None
        )
        assert not stored_path.exists()

        assert client.get("/auth/me", headers=auth_headers).status_code == 401
        assert (
            client.post(
                "/auth/login",
                json={"email": "user@example.com", "password": "rahasia123"},
            ).status_code
            == 401
        )

        assert db_session.get(CV, other_cv_id) is not None
        assert client.get("/auth/me", headers=other_headers).status_code == 200
    finally:
        set_embedder(None)


def test_delete_account_requires_authentication(client):
    assert client.delete("/auth/me").status_code == 401
