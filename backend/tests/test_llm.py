import json

import pytest

from app.core.config import Settings
from app.services.llm import (
    anonymize_profile,
    build_suggestions_prompt,
    fallback_suggestions,
    generate_suggestions,
    get_provider,
    parse_suggestions,
)
from app.services.scoring import ScoringInput, score_cv

PII_DATA = ScoringInput(
    name="Rizky Pratama",
    email="rizky.pratama@example.com",
    phone="+62 812-3456-7890",
    summary=(
        "Rizky Pratama, hubungi rizky.pratama@example.com atau +62 812-3456-7890. "
        "Portofolio: https://github.com/rizkypratama"
    ),
    links={
        "github": "https://github.com/rizkypratama",
        "linkedin": "https://linkedin.com/in/rizkypratama",
        "other": [],
    },
    education=[
        {
            "institution": "Universitas Rahasia",
            "degree": "S1 Ilmu Komputer",
            "period": "2016 - 2020",
            "details": ["Lulus dengan predikat cum laude"],
        }
    ],
    experience=[
        {
            "role": "Backend Engineer",
            "company": "PT Sangat Rahasia",
            "period": "2021 - Sekarang",
            "details": [
                "Rizky Pratama membangun API di rizky.pratama@example.com",
                "Hubungi +62 812-3456-7890 untuk referensi",
            ],
        }
    ],
    projects=[
        {
            "name": "Proyek Rizky",
            "period": "2023",
            "description": "Ditulis oleh Rizky Pratama",
        }
    ],
    skills=[
        {"name": "Python", "category": "Programming"},
        {"name": "FastAPI", "category": "Web"},
    ],
    raw_text="RINGKASAN\n" + ("Backend engineer. " * 30),
    page_count=1,
)


class FakeProvider:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.prompt = ""

    def complete(self, prompt: str) -> str:
        self.prompt = prompt
        if self.error is not None:
            raise self.error
        return self.response or ""


def test_anonymize_profile_removes_pii():
    payload = anonymize_profile(PII_DATA)
    serialized = json.dumps(payload, ensure_ascii=False)

    assert "rizky.pratama@example.com" not in serialized
    assert "812-3456-7890" not in serialized
    assert "Rizky" not in serialized
    assert "Pratama" not in serialized
    assert "github.com" not in serialized
    assert "linkedin.com" not in serialized
    assert "Universitas Rahasia" not in serialized
    assert "PT Sangat Rahasia" not in serialized
    assert "name" not in payload
    assert "email" not in payload
    assert "phone" not in payload
    assert "links" not in payload


def test_prompt_contains_scores_without_pii():
    result = score_cv(PII_DATA)
    prompt = build_suggestions_prompt(result, PII_DATA)

    assert f"Skor total: {result.total_score}/100" in prompt
    assert "rizky.pratama@example.com" not in prompt
    assert "812-3456-7890" not in prompt
    assert "Rizky" not in prompt
    assert "Pratama" not in prompt
    assert "github.com" not in prompt
    assert "PT Sangat Rahasia" not in prompt


def test_generate_suggestions_uses_valid_llm_response():
    response = json.dumps(
        [
            "Perkuat ringkasan dengan pencapaian terukur.",
            "Tambahkan angka pada bullet pengalaman.",
            "Cantumkan tautan portofolio yang relevan.",
        ]
    )
    provider = FakeProvider(response=response)

    result = generate_suggestions(PII_DATA, score_cv(PII_DATA), provider=provider)

    assert result["source"] == "llm"
    assert len(result["items"]) == 3
    assert result["items"][0].startswith("Perkuat ringkasan")
    assert "rizky.pratama@example.com" not in provider.prompt


def test_generate_suggestions_parses_code_fence():
    response = '```json\n["Saran satu yang jelas.", "Saran dua.", "Saran tiga."]\n```'
    provider = FakeProvider(response=response)

    result = generate_suggestions(PII_DATA, score_cv(PII_DATA), provider=provider)

    assert result["source"] == "llm"
    assert result["items"] == [
        "Saran satu yang jelas.",
        "Saran dua.",
        "Saran tiga.",
    ]


def test_generate_suggestions_falls_back_on_invalid_response():
    provider = FakeProvider(response="maaf saya tidak bisa")

    result = generate_suggestions(PII_DATA, score_cv(PII_DATA), provider=provider)

    assert result["source"] == "fallback"
    assert 3 <= len(result["items"]) <= 5


def test_generate_suggestions_falls_back_on_timeout():
    provider = FakeProvider(error=TimeoutError("timeout"))

    result = generate_suggestions(PII_DATA, score_cv(PII_DATA), provider=provider)

    assert result["source"] == "fallback"
    assert 3 <= len(result["items"]) <= 5


def test_generate_suggestions_falls_back_without_api_key():
    result = generate_suggestions(PII_DATA, score_cv(PII_DATA))

    assert result["source"] == "fallback"
    assert 3 <= len(result["items"]) <= 5


def test_parse_suggestions_requires_three_items():
    assert parse_suggestions('["Satu saran.", "Dua saran."]') == []
    assert parse_suggestions("bukan json") == []
    assert parse_suggestions(None) == []


def test_parse_suggestions_accepts_object_wrapper():
    raw = json.dumps(
        {"suggestions": ["Satu saran.", "Dua saran.", "Tiga saran."]}
    )

    assert len(parse_suggestions(raw)) == 3


def test_fallback_suggestions_prioritize_lowest_criteria():
    result = score_cv(ScoringInput())
    items = fallback_suggestions(result)

    assert 3 <= len(items) <= 5
    assert any("bagian" in item.lower() for item in items)


def test_get_provider_requires_api_key():
    assert get_provider(Settings(llm_api_key="")) is None
    assert get_provider(Settings(llm_api_key="  ")) is None


def test_get_provider_builds_openai_compatible_provider():
    provider = get_provider(
        Settings(
            llm_api_key="secret-key",
            llm_provider="openai",
            llm_model="gpt-test",
            llm_base_url="https://example.com/v1/",
        )
    )

    assert provider is not None
    assert provider.model == "gpt-test"
    assert provider.base_url == "https://example.com/v1"
    assert provider.api_key == "secret-key"


@pytest.mark.parametrize("count", [3, 4, 5])
def test_llm_items_are_capped_to_five(count):
    items = [f"Saran perbaikan nomor {index}." for index in range(count)]
    provider = FakeProvider(response=json.dumps(items))

    result = generate_suggestions(PII_DATA, score_cv(PII_DATA), provider=provider)

    assert len(result["items"]) == count
