import json
import re
from typing import Any, Protocol

import httpx

from app.core.config import Settings, settings
from app.services.scoring import ScoreResult, ScoringInput

LLM_MIN_SUGGESTIONS = 3
LLM_MAX_SUGGESTIONS = 5

SYSTEM_PROMPT = (
    "Anda adalah konsultan karier yang membantu memperbaiki CV. "
    "Berikan saran konkret dalam Bahasa Indonesia. "
    "Anda tidak boleh mengubah, menghitung ulang, atau menyebut skor baru."
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
PROFILE_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:github|linkedin)\.com/[^\s<>\"')]+",
    re.IGNORECASE,
)
PHONE_RE = re.compile(
    r"(?<!\d)(?:(?:\+62|62|0)8[\s.\-]?(?:\d[\s.\-]?){6,11}\d"
    r"|\+\d{1,3}[\s.\-]?(?:\(\d{2,4}\)|\d{2,4})[\s.\-]\d{3,4}[\s.\-]?\d{3,4})(?!\d)"
)
CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

FALLBACK_TEMPLATES = {
    "section_completeness": (
        "Lengkapi bagian yang masih kosong agar perekrut mendapat gambaran utuh."
    ),
    "description_quality": (
        "Tulis ulang bullet pencapaian dengan kata kerja aksi di awal dan "
        "sertakan angka atau hasil terukur."
    ),
    "ats_readability": (
        "Gunakan heading standar, hindari tabel/kolom rumit, dan pastikan "
        "seluruh teks CV bisa diekstrak mesin ATS."
    ),
    "skills_relevance": (
        "Tambahkan skill teknis yang relevan dengan target posisi dan "
        "variasikan kategori keahlian."
    ),
    "format_length": (
        "Jaga panjang CV 1-2 halaman, samakan format tanggal, dan cantumkan "
        "tautan GitHub serta LinkedIn."
    ),
}

GENERIC_SUGGESTIONS = (
    "Sesuaikan ringkasan profil dengan posisi yang dilamar agar relevansi "
    "langsung terlihat.",
    "Urutkan pengalaman dari yang paling relevan dan tonjolkan pencapaian "
    "terbesar di bagian atas.",
    "Periksa kembali ejaan, konsistensi istilah, dan format sebelum mengirim "
    "lamaran.",
)


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str: ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


def get_provider(settings_obj: Settings | None = None) -> LLMProvider | None:
    active = settings_obj or settings
    key = (active.llm_api_key or "").strip()
    name = (active.llm_provider or "").strip().lower()

    if not key or name in {"", "none", "disabled", "off"}:
        return None

    return OpenAICompatibleProvider(
        api_key=key,
        model=active.llm_model,
        base_url=active.llm_base_url,
        timeout=active.llm_timeout_seconds,
    )


def redact_text(
    text: Any,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> str:
    value = str(text or "")
    if not value:
        return ""

    if email and email.strip():
        value = re.sub(
            re.escape(email.strip()), "[email]", value, flags=re.IGNORECASE
        )
    if phone and phone.strip():
        value = re.sub(
            re.escape(phone.strip()), "[telepon]", value, flags=re.IGNORECASE
        )

    value = EMAIL_RE.sub("[email]", value)
    value = PROFILE_URL_RE.sub("[tautan]", value)
    value = URL_RE.sub("[tautan]", value)
    value = PHONE_RE.sub("[telepon]", value)

    if name and name.strip():
        cleaned_name = " ".join(name.split())
        value = re.sub(
            re.escape(cleaned_name), "[nama]", value, flags=re.IGNORECASE
        )
        for token in cleaned_name.split():
            if len(token) >= 4:
                value = re.sub(
                    re.escape(token), "[nama]", value, flags=re.IGNORECASE
                )

    return value


def _redacted_items(
    items: list[Any], data: ScoringInput, fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        entry: dict[str, Any] = {}
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                entry[field] = [
                    redact_text(
                        value_item,
                        name=data.name,
                        email=data.email,
                        phone=data.phone,
                    )
                    for value_item in value
                ]
            elif value:
                entry[field] = redact_text(
                    value,
                    name=data.name,
                    email=data.email,
                    phone=data.phone,
                )
        if entry:
            result.append(entry)
    return result


def anonymize_profile(data: ScoringInput) -> dict[str, Any]:
    return {
        "summary": redact_text(
            data.summary,
            name=data.name,
            email=data.email,
            phone=data.phone,
        ),
        "education": _redacted_items(
            data.education, data, ("degree", "period", "details")
        ),
        "experience": _redacted_items(
            data.experience, data, ("role", "period", "details")
        ),
        "projects": _redacted_items(
            data.projects, data, ("name", "period", "description")
        ),
        "skills": [
            skill.get("name")
            for skill in data.skills
            if (skill.get("name") or "").strip()
        ],
    }


def build_suggestions_prompt(
    result: ScoreResult, data: ScoringInput
) -> str:
    criteria = [
        {
            "kriteria": criterion.label,
            "skor": criterion.score,
            "maks": criterion.max_score,
            "alasan": criterion.reasons,
        }
        for criterion in result.criteria
    ]
    profile = anonymize_profile(data)

    return (
        "Berikut hasil penilaian CV yang sudah dihitung oleh sistem. "
        "Jangan mengubah angka apa pun.\n\n"
        f"Skor total: {result.total_score}/100\n"
        f"Rincian kriteria: {json.dumps(criteria, ensure_ascii=False)}\n"
        f"Profil teranonimisasi: {json.dumps(profile, ensure_ascii=False)}\n\n"
        "Buat 3 sampai 5 saran perbaikan CV yang spesifik, praktis, dan "
        "berurutan dari yang paling berdampak. Balas HANYA dengan array JSON "
        'berisi string, contoh: ["saran 1", "saran 2", "saran 3"].'
    )


def parse_suggestions(raw: Any) -> list[str]:
    if not isinstance(raw, str):
        return []

    cleaned = CODE_FENCE_RE.sub("", raw.strip()).strip()
    if not cleaned:
        return []

    data: Any
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []

    if isinstance(data, dict):
        data = data.get("suggestions") or data.get("items") or []

    if not isinstance(data, list):
        return []

    items: list[str] = []
    for item in data:
        if not isinstance(item, str):
            continue
        text = " ".join(item.split()).strip()
        if len(text) < 8:
            continue
        if text not in items:
            items.append(text)

    if len(items) < LLM_MIN_SUGGESTIONS:
        return []
    return items[:LLM_MAX_SUGGESTIONS]


def _severity(criterion: Any) -> float:
    if criterion.max_score <= 0:
        return 0.0
    return criterion.score / criterion.max_score


def fallback_suggestions(result: ScoreResult) -> list[str]:
    ordered = sorted(result.criteria, key=_severity)

    items: list[str] = []
    for criterion in ordered:
        if criterion.score >= criterion.max_score:
            continue
        template = FALLBACK_TEMPLATES.get(criterion.key)
        if not template:
            continue
        if criterion.key == "section_completeness":
            missing = [
                reason.split(":", 1)[0].strip()
                for reason in criterion.reasons
                if "belum ada" in reason
            ]
            if missing:
                template = (
                    "Lengkapi bagian berikut agar profil lebih utuh: "
                    + ", ".join(missing)
                    + "."
                )
        if template not in items:
            items.append(template)
        if len(items) >= LLM_MAX_SUGGESTIONS:
            break

    for suggestion in GENERIC_SUGGESTIONS:
        if len(items) >= LLM_MIN_SUGGESTIONS:
            break
        if suggestion not in items:
            items.append(suggestion)

    return items[:LLM_MAX_SUGGESTIONS]


def generate_suggestions(
    data: ScoringInput,
    result: ScoreResult,
    provider: LLMProvider | None = None,
    settings_obj: Settings | None = None,
) -> dict[str, Any]:
    active = provider
    if active is None:
        active = get_provider(settings_obj)

    if active is not None:
        try:
            prompt = build_suggestions_prompt(result, data)
            items = parse_suggestions(active.complete(prompt))
        except Exception:
            items = []
        if items:
            return {"items": items, "source": "llm"}

    return {"items": fallback_suggestions(result), "source": "fallback"}
