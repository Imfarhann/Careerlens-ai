from pathlib import Path

import pytest

from app.services.nlp import (
    extract_email,
    extract_links,
    extract_phone,
    extract_profile,
    extract_skills,
    split_sections,
)
from app.services.parser import parse_document

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def profile_for(filename: str) -> dict:
    path = FIXTURES / filename
    text = parse_document(path.read_bytes(), path.suffix)
    return extract_profile(text)


def skill_names(profile: dict) -> set[str]:
    return {skill["name"] for skill in profile["skills"]}


@pytest.mark.parametrize("filename", ["indonesian.pdf", "indonesian.docx"])
def test_indonesian_profile_extraction(filename):
    profile = profile_for(filename)

    assert profile["name"] == "RIZKY PRATAMA"
    assert profile["email"] == "rizky.pratama@example.com"
    assert profile["phone"].endswith("7890")
    assert profile["links"]["github"] == "https://github.com/rizkypratama"
    assert "linkedin.com/in/rizkypratama" in profile["links"]["linkedin"]
    assert profile["summary"].startswith("Backend engineer")
    assert profile["education"][0]["institution"] == "Universitas Indonesia"
    assert profile["education"][0]["degree"] == "S1 Ilmu Komputer"
    assert profile["education"][0]["period"] == "2016 - 2020"
    assert profile["experience"][0]["role"] == "Backend Engineer"
    assert profile["experience"][0]["company"] == "PT Teknologi Nusantara"
    assert profile["experience"][0]["period"] == "2021 - Sekarang"
    assert len(profile["experience"][0]["details"]) == 3
    assert profile["projects"][0]["name"] == "CareerLens API"
    assert skill_names(profile) >= {
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "Communication",
    }


@pytest.mark.parametrize("filename", ["english.pdf", "english.docx"])
def test_english_profile_extraction(filename):
    profile = profile_for(filename)

    assert profile["name"] == "ALEX MORGAN"
    assert profile["email"] == "alex.morgan@example.com"
    assert profile["phone"] == "+1 (415) 555-0132"
    assert profile["links"]["github"] == "https://github.com/alexmorgan"
    assert "linkedin.com/in/alexmorgan" in profile["links"]["linkedin"]
    assert profile["education"][0]["institution"] == (
        "University of California, Berkeley"
    )
    assert profile["experience"][0]["role"] == "Software Engineer"
    assert profile["experience"][0]["company"] == "Acme Corp"
    assert profile["projects"][0]["name"] == "OpenBoard"
    assert skill_names(profile) >= {
        "React",
        "TypeScript",
        "Node.js",
        "Kubernetes",
        "Teamwork",
    }


@pytest.mark.parametrize("filename", ["messy.pdf", "messy.docx"])
def test_messy_profile_extraction(filename):
    profile = profile_for(filename)

    assert profile["name"] == "SITI NURHALIZA"
    assert profile["email"] == "siti.nurhaliza@example.com"
    assert profile["phone"] == "081298765432"
    assert profile["links"]["github"] == "https://github.com/sitinurhaliza"
    assert profile["education"]
    assert profile["education"][0]["institution"].startswith(
        "Universitas Brawijaya"
    )
    assert profile["education"][0]["period"] == "2018-2022"
    assert profile["experience"]
    assert profile["projects"][0]["name"].startswith("Dashboard Penjualan")
    assert profile["projects"][0]["period"] == "2023"
    assert skill_names(profile) >= {
        "Microsoft Excel",
        "SQL",
        "Power BI",
        "Communication",
    }


def test_messy_docx_keeps_extra_sections():
    profile = profile_for("messy.docx")

    assert profile["extra"]["certifications"] == ["Google Data Analytics"]


def test_section_detection_indonesian_and_english():
    text = """Nama Lengkap
PENDIDIKAN
Universitas Contoh
2018 - 2022
PENGALAMAN KERJA: Engineer di PT Contoh 2022-sekarang
Projects
Portfolio App
2024
Skills: Python, Docker"""

    _, sections = split_sections(text)

    assert "education" in sections
    assert "experience" in sections
    assert "projects" in sections
    assert "skills" in sections


def test_extract_skills_handles_aliases_and_boundaries():
    text = "Saya memakai JS, Postgres, k8s, dan CI/CD setiap hari."

    names = {skill["name"] for skill in extract_skills(text)}

    assert {"JavaScript", "PostgreSQL", "Kubernetes", "CI/CD"} <= names


def test_extract_skills_does_not_match_substrings():
    text = "JavaScript dan MySQL saja."

    names = {skill["name"] for skill in extract_skills(text)}

    assert "JavaScript" in names
    assert "MySQL" in names
    assert "Java" not in names
    assert "SQL" not in names


def test_extract_skills_avoids_duplicate_spans():
    names = {skill["name"] for skill in extract_skills("React Native dan React")}

    assert "React Native" in names


def test_extract_contact_helpers():
    text = (
        "Email: budi@example.com\n"
        "Telepon: +62 812 3456 7890\n"
        "https://github.com/budi dan https://portofolio.dev/budi"
    )

    assert extract_email(text) == "budi@example.com"
    assert "812" in extract_phone(text)
    links = extract_links(text)
    assert links["github"] == "https://github.com/budi"
    assert "https://portofolio.dev/budi" in links["other"]
