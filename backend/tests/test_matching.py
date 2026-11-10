from types import SimpleNamespace

import pytest

from app.services.matching import (
    JobCandidate,
    JobSkillRef,
    SentenceTransformerEmbedder,
    build_profile_text,
    clip_similarity,
    combine_score,
    compute_skill_coverage,
    cosine_similarity,
    get_embedder,
    rank_candidates,
    set_embedder,
)


class MappingEmbedder:
    def __init__(self, vectors):
        self.vectors = vectors
        self.calls = []

    def embed(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        return [list(self.vectors[text]) for text in texts]


def test_weighted_coverage_matches_manual_math():
    refs = [
        JobSkillRef("a", "A", is_required=True),
        JobSkillRef("b", "B", is_required=True),
        JobSkillRef("c", "C", is_required=False),
    ]

    coverage, matched, missing, missing_refs = compute_skill_coverage(
        {"a", "c"}, refs
    )

    assert coverage == pytest.approx(3 / 5)
    assert matched == ["A", "C"]
    assert missing == ["B"]
    assert [ref.skill_id for ref in missing_refs] == ["b"]


def test_user_without_skills_has_zero_coverage():
    refs = [JobSkillRef("a", "A", is_required=True)]

    coverage, matched, missing, _ = compute_skill_coverage(set(), refs)

    assert coverage == 0.0
    assert matched == []
    assert missing == ["A"]


def test_job_without_skills_has_full_coverage():
    coverage, matched, missing, missing_refs = compute_skill_coverage(
        set(), []
    )

    assert coverage == 1.0
    assert matched == []
    assert missing == []
    assert missing_refs == []


def test_duplicate_skill_prefers_required_weight():
    refs = [
        JobSkillRef("a", "A", is_required=False),
        JobSkillRef("a", "A", is_required=True),
    ]

    coverage, _, missing, _ = compute_skill_coverage({"a"}, refs)

    assert coverage == 1.0
    assert missing == []


def test_cosine_similarity_and_clipping():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 0.0]) == 0.0

    assert clip_similarity(-0.4) == 0.0
    assert clip_similarity(0.7) == pytest.approx(0.7)
    assert clip_similarity(1.3) == 1.0


def test_combine_score_uses_sixty_forty_split():
    assert combine_score(0.5, 1.0) == pytest.approx(0.7)
    assert combine_score(1.0, 0.0) == pytest.approx(0.6)


def test_rank_candidates_sorts_by_match_score_descending():
    candidates = [
        JobCandidate(
            job_id="first",
            title="First",
            description="alpha",
            skills=(
                JobSkillRef("a", "A", is_required=True),
                JobSkillRef("c", "C", is_required=True),
            ),
        ),
        JobCandidate(
            job_id="second",
            title="Second",
            description="beta",
            skills=(
                JobSkillRef("a", "A", is_required=True),
                JobSkillRef("b", "B", is_required=True),
            ),
        ),
    ]
    embedder = MappingEmbedder(
        {"profile": [1.0, 0.0], "alpha": [1.0, 0.0], "beta": [0.0, 1.0]}
    )

    results = rank_candidates("profile", {"a", "b"}, candidates, embedder)

    assert [result.job_id for result in results] == ["first", "second"]
    first, second = results
    assert first.skill_coverage == pytest.approx(0.5)
    assert first.semantic_similarity == pytest.approx(1.0)
    assert first.match_score == pytest.approx(0.7)
    assert second.skill_coverage == pytest.approx(1.0)
    assert second.semantic_similarity == pytest.approx(0.0)
    assert second.match_score == pytest.approx(0.6)


def test_empty_profile_text_gives_zero_semantic_similarity():
    candidate = JobCandidate(
        job_id="job",
        title="Job",
        description="alpha",
        skills=(),
        embedding=(1.0, 0.0),
    )
    embedder = MappingEmbedder({})

    results = rank_candidates("   ", set(), [candidate], embedder)

    assert results[0].semantic_similarity == 0.0
    assert results[0].match_score == pytest.approx(0.6)


def test_build_profile_text_excludes_personal_data():
    profile = SimpleNamespace(
        name="Budi Santoso",
        email="budi@example.com",
        phone="081234567890",
        summary="Kontak budi@example.com",
        user_skills=[
            SimpleNamespace(skill=SimpleNamespace(name="Python")),
            SimpleNamespace(skill=SimpleNamespace(name="PostgreSQL")),
        ],
        experience=[
            {
                "role": "Backend Engineer",
                "company": "Rahasia Corp",
                "details": ["Membangun API internal"],
            }
        ],
        projects=[
            {
                "name": "Sistem Kasir",
                "description": "Aplikasi kasir untuk toko kecil",
            }
        ],
    )

    text = build_profile_text(profile)

    assert "Python" in text
    assert "PostgreSQL" in text
    assert "Backend Engineer" in text
    assert "Sistem Kasir" in text
    assert "Budi Santoso" not in text
    assert "budi@example.com" not in text
    assert "081234567890" not in text
    assert "Rahasia Corp" not in text


def test_real_embedder_stays_lazy_until_first_use():
    embedder = SentenceTransformerEmbedder()

    assert embedder._model is None


def test_embedder_can_be_replaced_and_restored():
    original = get_embedder()
    replacement = MappingEmbedder({})
    set_embedder(replacement)

    try:
        assert get_embedder() is replacement
    finally:
        set_embedder(original)
