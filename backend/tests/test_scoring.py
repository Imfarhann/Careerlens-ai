import pytest

from app.services.scoring import (
    ATS_CRITERIA_MAX,
    DESCRIPTION_CRITERIA_MAX,
    FORMAT_CRITERIA_MAX,
    SECTION_CRITERIA_MAX,
    SKILLS_CRITERIA_MAX,
    TOTAL_MAX_SCORE,
    ScoringInput,
    score_ats_readability,
    score_cv,
    score_description_quality,
    score_format_length,
    score_section_completeness,
    score_skills_relevance,
)

FILLER = (
    "Membangun layanan backend yang andal, menulis dokumentasi teknis, "
    "dan berkolaborasi dengan tim produk untuk mengirim fitur tepat waktu. "
)


def perfect_input() -> ScoringInput:
    raw_text = f"""RINGKASAN
Backend engineer dengan pengalaman membangun API dan sistem terdistribusi.

PENDIDIKAN
Universitas Indonesia
S1 Ilmu Komputer
2016 - 2020

PENGALAMAN KERJA
Backend Engineer
PT Teknologi Nusantara
2021 - Sekarang
- Membangun REST API dengan 3 layanan utama
- Mengurangi latensi 40 persen

PROYEK
CareerLens API
2022 - 2023
- Membuat dashboard dengan 5 grafik interaktif

KEAHLIAN
Python, FastAPI, PostgreSQL, Docker, Redis, AWS, Git, React, TypeScript, "
Node.js, SQL, Communication

{FILLER * 6}"""

    return ScoringInput(
        name="Budi Santoso",
        email="budi@example.com",
        phone="+62 812 3456 7890",
        summary="Backend engineer yang fokus pada API yang cepat dan andal.",
        links={
            "github": "https://github.com/budi",
            "linkedin": "https://linkedin.com/in/budi",
            "other": [],
        },
        education=[
            {
                "institution": "Universitas Indonesia",
                "degree": "S1 Ilmu Komputer",
                "period": "2016 - 2020",
                "details": [],
            }
        ],
        experience=[
            {
                "role": "Backend Engineer",
                "company": "PT Teknologi Nusantara",
                "period": "2021 - Sekarang",
                "details": [
                    "Membangun REST API dengan 3 layanan utama",
                    "Mengurangi latensi 40 persen",
                ],
            }
        ],
        projects=[
            {
                "name": "CareerLens API",
                "period": "2022 - 2023",
                "description": "- Membuat dashboard dengan 5 grafik interaktif",
            }
        ],
        skills=[
            {"name": "Python", "category": "Programming"},
            {"name": "FastAPI", "category": "Web"},
            {"name": "PostgreSQL", "category": "Database"},
            {"name": "Docker", "category": "DevOps"},
            {"name": "Redis", "category": "Database"},
            {"name": "AWS", "category": "DevOps"},
            {"name": "Git", "category": "Tools"},
            {"name": "React", "category": "Web"},
            {"name": "TypeScript", "category": "Programming"},
            {"name": "Node.js", "category": "Web"},
            {"name": "SQL", "category": "Programming"},
            {"name": "Communication", "category": "Soft Skill"},
        ],
        raw_text=raw_text,
        page_count=2,
        has_tables=False,
        has_images=False,
    )


def test_total_max_score_is_one_hundred():
    assert TOTAL_MAX_SCORE == 100
    assert (
        SECTION_CRITERIA_MAX
        + DESCRIPTION_CRITERIA_MAX
        + ATS_CRITERIA_MAX
        + SKILLS_CRITERIA_MAX
        + FORMAT_CRITERIA_MAX
        == 100
    )


def test_perfect_cv_scores_one_hundred():
    result = score_cv(perfect_input())

    assert result.total_score == 100
    scores = {criterion.key: criterion.score for criterion in result.criteria}
    assert scores == {
        "section_completeness": 25,
        "description_quality": 25,
        "ats_readability": 20,
        "skills_relevance": 15,
        "format_length": 15,
    }
    assert sum(criterion.max_score for criterion in result.criteria) == 100


def test_empty_cv_scores_zero():
    result = score_cv(ScoringInput())

    assert result.total_score == 0
    assert all(criterion.score == 0 for criterion in result.criteria)


def test_section_completeness_scores_five_per_section():
    contact_only = ScoringInput(name="Budi", email="budi@example.com")

    score, maximum, reasons = score_section_completeness(contact_only)

    assert (score, maximum) == (5, 25)
    assert any("Kontak: lengkap" in reason for reason in reasons)
    assert any("Pendidikan: belum ada" in reason for reason in reasons)


def test_section_completeness_accepts_projects_instead_of_experience():
    data = ScoringInput(
        name="Budi",
        email="budi@example.com",
        projects=[{"name": "Proyek Akhir", "period": "2023"}],
    )

    score, _, reasons = score_section_completeness(data)

    assert score == 10
    assert any("Pengalaman/proyek: lengkap" in reason for reason in reasons)


def test_description_quality_combines_action_verbs_and_metrics():
    data = ScoringInput(
        experience=[
            {
                "details": [
                    "Membangun API dengan 3 layanan",
                    "Mengurangi latensi 40 persen",
                    "Merancang arsitektur modular",
                    "Dokumentasi lengkap untuk 5 tim",
                ]
            }
        ]
    )

    score, maximum, reasons = score_description_quality(data)

    assert (score, maximum) == (19, 25)
    assert any("3/4 bullet diawali kata kerja aksi" in reason for reason in reasons)
    assert any("3/4 bullet memuat angka" in reason for reason in reasons)


def test_description_quality_zero_bullets_scores_zero():
    score, maximum, reasons = score_description_quality(ScoringInput())

    assert (score, maximum) == (0, 25)
    assert any("Tidak ada bullet" in reason for reason in reasons)


def test_description_quality_all_action_verbs_and_metrics_scores_full():
    data = ScoringInput(
        experience=[
            {"details": ["Built 2 APIs", "Led 4 engineers"]},
        ]
    )

    score, maximum, _ = score_description_quality(data)

    assert (score, maximum) == (25, 25)


def test_ats_short_text_scores_zero():
    score, maximum, reasons = score_ats_readability(
        ScoringInput(raw_text="Terlalu pendek")
    )

    assert (score, maximum) == (0, 20)
    assert any("terlalu pendek" in reason.lower() for reason in reasons)


def test_ats_penalizes_tables():
    data = perfect_input()
    data.has_tables = True

    score, maximum, reasons = score_ats_readability(data)

    assert (score, maximum) == (17, 20)
    assert any("tabel" in reason.lower() for reason in reasons)


def test_ats_penalizes_broken_characters():
    data = perfect_input()
    data.raw_text = data.raw_text + "\ufffd\ufffd\ufffd\ufffd"

    score, _, reasons = score_ats_readability(data)

    assert score == 16
    assert any("karakter rusak" in reason for reason in reasons)


def test_skills_relevance_single_skill():
    data = ScoringInput(skills=[{"name": "Python", "category": "Programming"}])

    score, maximum, _ = score_skills_relevance(data)

    assert (score, maximum) == (2, 15)


def test_skills_relevance_counts_and_categories():
    data = ScoringInput(
        skills=[
            {"name": "Python", "category": "Programming"},
            {"name": "React", "category": "Web"},
            {"name": "PostgreSQL", "category": "Database"},
            {"name": "Docker", "category": "DevOps"},
            {"name": "Git", "category": "Tools"},
        ]
    )

    score, maximum, reasons = score_skills_relevance(data)

    assert (score, maximum) == (11, 15)
    assert any("5 skill terdeteksi" in reason for reason in reasons)


def test_skills_relevance_full_marks():
    score, maximum, _ = score_skills_relevance(perfect_input())

    assert (score, maximum) == (15, 15)


@pytest.mark.parametrize(
    "page_count, expected",
    [(1, 7), (2, 7), (3, 4), (4, 2)],
)
def test_format_page_points(page_count, expected):
    data = ScoringInput(raw_text="isi cv", page_count=page_count)

    score, _, _ = score_format_length(data)

    assert score == expected


def test_format_links_add_four_points():
    data = ScoringInput(
        raw_text="isi cv",
        page_count=2,
        links={
            "github": "https://github.com/budi",
            "linkedin": "https://linkedin.com/in/budi",
        },
    )

    score, _, reasons = score_format_length(data)

    assert score == 11
    assert any("GitHub tersedia" in reason for reason in reasons)
    assert any("LinkedIn tersedia" in reason for reason in reasons)


def test_format_consistent_dates_score_full():
    data = ScoringInput(
        education=[{"period": "2016 - 2020"}],
        experience=[{"period": "2021 - Sekarang"}],
        projects=[{"period": "2022 - 2023"}],
    )

    score, maximum, reasons = score_format_length(data)

    assert (score, maximum) == (4, 15)
    assert any("konsisten" in reason for reason in reasons)


def test_format_inconsistent_dates_get_partial_points():
    data = ScoringInput(
        education=[{"period": "2016 - 2020"}],
        experience=[{"period": "2023"}],
    )

    score, _, reasons = score_format_length(data)

    assert score == 2
    assert any("tidak konsisten" in reason for reason in reasons)


def test_format_estimates_pages_from_word_count():
    data = ScoringInput(raw_text=" ".join(["kata"] * 900))

    score, _, reasons = score_format_length(data)

    assert score == 7
    assert any("perkiraan" in reason for reason in reasons)


@pytest.mark.parametrize(
    "data",
    [
        ScoringInput(),
        ScoringInput(name="Budi", email="budi@example.com"),
        ScoringInput(
            summary="Ringkasan",
            education=[{"period": "2020"}],
            experience=[{"period": "2021", "details": ["Membuat 2 fitur"]}],
            skills=[{"name": "Python", "category": "Programming"}],
            links={"github": "https://github.com/budi"},
            raw_text="RINGKASAN\n" + FILLER * 10,
            page_count=2,
        ),
        perfect_input(),
    ],
)
def test_total_score_always_between_zero_and_one_hundred(data):
    result = score_cv(data)

    assert 0 <= result.total_score <= 100
