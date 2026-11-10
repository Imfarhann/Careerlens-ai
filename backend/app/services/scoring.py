import math
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.nlp import split_sections

SECTION_CRITERIA_MAX = 25
SECTION_POINTS = 5
SECTION_LABELS = {
    "contact": "Kontak",
    "education": "Pendidikan",
    "experience": "Pengalaman/proyek",
    "skills": "Keahlian",
    "summary": "Ringkasan",
}

DESCRIPTION_CRITERIA_MAX = 25
DESCRIPTION_ACTION_WEIGHT = 0.5
DESCRIPTION_METRIC_WEIGHT = 0.5
ACTION_VERBS = frozenset(
    {
        "membangun",
        "mengembangkan",
        "merancang",
        "mendesain",
        "membuat",
        "memimpin",
        "mengelola",
        "meningkatkan",
        "mengoptimalkan",
        "menganalisis",
        "mengimplementasikan",
        "mengotomatiskan",
        "meluncurkan",
        "memigrasikan",
        "menguji",
        "memelihara",
        "mengurangi",
        "mempercepat",
        "mengintegrasikan",
        "menciptakan",
        "menyusun",
        "mengoordinasikan",
        "melatih",
        "membimbing",
        "mencapai",
        "menghasilkan",
        "mengawasi",
        "mengevaluasi",
        "memperluas",
        "menstandarkan",
        "mengamankan",
        "mengukur",
        "memetakan",
        "menyelesaikan",
        "built",
        "led",
        "developed",
        "designed",
        "created",
        "implemented",
        "improved",
        "increased",
        "reduced",
        "optimized",
        "automated",
        "launched",
        "migrated",
        "managed",
        "analyzed",
        "delivered",
        "architected",
        "integrated",
        "mentored",
        "coordinated",
        "achieved",
        "maintained",
        "tested",
        "deployed",
        "streamlined",
        "scaled",
        "established",
        "drove",
        "spearheaded",
        "introduced",
        "refactored",
        "monitored",
        "resolved",
        "negotiated",
        "presented",
    }
)
METRIC_RE = re.compile(r"\d")

ATS_CRITERIA_MAX = 20
ATS_MIN_TEXT_CHARS = 200
ATS_TEXT_POINTS_MAX = 6
ATS_HEADING_POINTS_MAX = 5
ATS_TABLE_POINTS_MAX = 5
ATS_TABLE_POINTS = 5
ATS_TABLE_PENALTY = 2
ATS_BROKEN_POINTS_MAX = 4
ATS_BROKEN_POINTS = 4
ATS_BROKEN_SOFT_POINTS = 2
ATS_BROKEN_CHAR_LIMIT = 3
ATS_TEXT_THRESHOLDS = ((600, 6), (300, 4), (200, 2))
ATS_HEADING_THRESHOLDS = ((4, 5), (3, 4), (2, 2), (1, 1))
STANDARD_SECTIONS = (
    "summary",
    "education",
    "experience",
    "projects",
    "skills",
)
SECTION_NAME_ID = {
    "summary": "ringkasan",
    "education": "pendidikan",
    "experience": "pengalaman",
    "projects": "proyek",
    "skills": "keahlian",
}
BROKEN_CHAR_RE = re.compile(r"[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]")

SKILLS_CRITERIA_MAX = 15
SKILL_COUNT_MAX = 8
SKILL_CATEGORY_MAX = 7
SKILL_COUNT_THRESHOLDS = ((12, 8), (8, 6), (5, 4), (2, 2), (1, 1))
SKILL_CATEGORY_THRESHOLDS = ((4, 7), (3, 5), (2, 3), (1, 1))

FORMAT_CRITERIA_MAX = 15
FORMAT_PAGE_MAX = 7
FORMAT_LINK_MAX = 4
FORMAT_DATE_MAX = 4
WORDS_PER_PAGE = 450
MONTH_PATTERN = (
    r"(?:jan|feb|mar|apr|may|mei|jun|jul|aug|agu|sep|oct|okt|nov|dec|des)"
    r"[a-z]*\.?"
)
MONTH_RE = re.compile(rf"\b{MONTH_PATTERN}\s+\d{{4}}", re.IGNORECASE)
YEAR_RANGE_RE = re.compile(
    rf"(?:19|20)\d{{2}}\s*(?:-|–|—|s\.?d\.?|to|until|sampai|hingga)\s*"
    rf"(?:(?:19|20)\d{{2}}|sekarang|present|now|current)",
    re.IGNORECASE,
)
YEAR_ONLY_RE = re.compile(r"^(?:19|20)\d{2}$")


@dataclass
class ScoringInput:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    links: dict[str, Any] = field(default_factory=dict)
    education: list[dict[str, Any]] = field(default_factory=list)
    experience: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""
    page_count: int | None = None
    has_tables: bool = False
    has_images: bool = False


@dataclass(frozen=True)
class CriterionResult:
    key: str
    label: str
    score: int
    max_score: int
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "score": self.score,
            "max_score": self.max_score,
            "reasons": self.reasons,
        }


@dataclass(frozen=True)
class ScoreResult:
    total_score: int
    criteria: list[CriterionResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_score": self.total_score,
            "criteria": [criterion.to_dict() for criterion in self.criteria],
        }


def _threshold_points(
    value: int, thresholds: tuple[tuple[int, int], ...]
) -> int:
    for minimum, points in thresholds:
        if value >= minimum:
            return points
    return 0


def _percentage(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((part / total) * 100)


def _first_word(text: str) -> str:
    match = re.match(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", text.strip())
    return match.group(0).casefold() if match else ""


def _collect_bullets(data: ScoringInput) -> list[str]:
    bullets: list[str] = []

    for item in data.experience:
        for detail in item.get("details") or []:
            cleaned = str(detail).strip().lstrip("-•*").strip()
            if cleaned:
                bullets.append(cleaned)

    for item in data.projects:
        description = str(item.get("description") or "")
        for line in description.splitlines():
            cleaned = line.strip().lstrip("-•*").strip()
            if cleaned:
                bullets.append(cleaned)

    return bullets


def score_section_completeness(
    data: ScoringInput,
) -> tuple[int, int, list[str]]:
    contact_complete = bool(
        (data.name or "").strip()
        and ((data.email or "").strip() or (data.phone or "").strip())
    )
    checks = (
        (SECTION_LABELS["contact"], contact_complete),
        (SECTION_LABELS["education"], bool(data.education)),
        (
            SECTION_LABELS["experience"],
            bool(data.experience) or bool(data.projects),
        ),
        (SECTION_LABELS["skills"], bool(data.skills)),
        (
            SECTION_LABELS["summary"],
            bool((data.summary or "").strip()),
        ),
    )

    score = 0
    reasons: list[str] = []
    for label, present in checks:
        if present:
            score += SECTION_POINTS
            reasons.append(f"{label}: lengkap (+{SECTION_POINTS})")
        else:
            reasons.append(f"{label}: belum ada (0/{SECTION_POINTS})")

    return score, SECTION_CRITERIA_MAX, reasons


def score_description_quality(
    data: ScoringInput,
) -> tuple[int, int, list[str]]:
    bullets = _collect_bullets(data)
    total = len(bullets)

    if total == 0:
        return (
            0,
            DESCRIPTION_CRITERIA_MAX,
            [
                "Tidak ada bullet pencapaian pada pengalaman atau proyek. "
                "Tambahkan poin yang diawali kata kerja aksi dan memuat hasil terukur."
            ],
        )

    action_count = sum(
        1 for bullet in bullets if _first_word(bullet) in ACTION_VERBS
    )
    metric_count = sum(1 for bullet in bullets if METRIC_RE.search(bullet))

    action_ratio = action_count / total
    metric_ratio = metric_count / total
    score = round(
        DESCRIPTION_CRITERIA_MAX
        * (
            DESCRIPTION_ACTION_WEIGHT * action_ratio
            + DESCRIPTION_METRIC_WEIGHT * metric_ratio
        )
    )

    reasons = [
        f"{action_count}/{total} bullet diawali kata kerja aksi "
        f"({_percentage(action_count, total)}%)",
        f"{metric_count}/{total} bullet memuat angka atau hasil terukur "
        f"({_percentage(metric_count, total)}%)",
    ]
    return score, DESCRIPTION_CRITERIA_MAX, reasons


def score_ats_readability(
    data: ScoringInput,
) -> tuple[int, int, list[str]]:
    text = data.raw_text or ""
    text_length = len(text.strip())

    if text_length < ATS_MIN_TEXT_CHARS:
        return (
            0,
            ATS_CRITERIA_MAX,
            [
                f"Teks CV terlalu pendek atau tidak terekstrak dengan baik "
                f"({text_length} karakter, minimal {ATS_MIN_TEXT_CHARS})."
            ],
        )

    score = 0
    reasons: list[str] = []

    text_points = _threshold_points(text_length, ATS_TEXT_THRESHOLDS)
    score += text_points
    reasons.append(
        f"Teks terekstrak {text_length} karakter "
        f"(+{text_points}/{ATS_TEXT_POINTS_MAX})"
    )

    _, sections = split_sections(text)
    detected = [name for name in STANDARD_SECTIONS if name in sections]
    heading_points = _threshold_points(
        len(detected), ATS_HEADING_THRESHOLDS
    )
    score += heading_points
    heading_names = (
        ", ".join(SECTION_NAME_ID[name] for name in detected) or "tidak ada"
    )
    reasons.append(
        f"{len(detected)} heading standar terdeteksi: {heading_names} "
        f"(+{heading_points}/{ATS_HEADING_POINTS_MAX})"
    )

    if data.has_tables:
        score += ATS_TABLE_PENALTY
        reasons.append(
            f"Terdeteksi tabel yang bisa membingungkan ATS "
            f"(+{ATS_TABLE_PENALTY}/{ATS_TABLE_POINTS_MAX})"
        )
    else:
        score += ATS_TABLE_POINTS
        reasons.append(
            f"Tidak ada tabel kompleks "
            f"(+{ATS_TABLE_POINTS}/{ATS_TABLE_POINTS_MAX})"
        )

    broken_count = len(BROKEN_CHAR_RE.findall(text))
    if broken_count == 0:
        broken_points = ATS_BROKEN_POINTS
        broken_reason = "Tidak ada karakter rusak"
    elif broken_count <= ATS_BROKEN_CHAR_LIMIT:
        broken_points = ATS_BROKEN_SOFT_POINTS
        broken_reason = f"{broken_count} karakter rusak terdeteksi"
    else:
        broken_points = 0
        broken_reason = (
            f"{broken_count} karakter rusak mengganggu keterbacaan"
        )
    score += broken_points
    reasons.append(
        f"{broken_reason} (+{broken_points}/{ATS_BROKEN_POINTS_MAX})"
    )

    if data.has_images:
        reasons.append(
            "Dokumen memuat gambar; pastikan teks utama tetap berupa teks."
        )

    return score, ATS_CRITERIA_MAX, reasons


def score_skills_relevance(
    data: ScoringInput,
) -> tuple[int, int, list[str]]:
    skill_names = {
        (skill.get("name") or "").strip().casefold()
        for skill in data.skills
        if (skill.get("name") or "").strip()
    }
    categories = {
        (skill.get("category") or "").strip()
        for skill in data.skills
        if (skill.get("category") or "").strip()
    }

    count = len(skill_names)
    count_points = _threshold_points(count, SKILL_COUNT_THRESHOLDS)
    category_points = _threshold_points(
        len(categories), SKILL_CATEGORY_THRESHOLDS
    )
    score = count_points + category_points

    if count == 0:
        reasons = [
            "Belum ada skill yang terdeteksi (0/8 poin jumlah).",
            "Belum ada kategori skill (0/7 poin keragaman).",
        ]
    else:
        category_list = ", ".join(sorted(categories))
        reasons = [
            f"{count} skill terdeteksi (+{count_points}/{SKILL_COUNT_MAX})",
            f"{len(categories)} kategori skill: {category_list} "
            f"(+{category_points}/{SKILL_CATEGORY_MAX})",
        ]

    return score, SKILLS_CRITERIA_MAX, reasons


def _date_style(period: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(period)).strip()
    if not cleaned:
        return "empty"
    if MONTH_RE.search(cleaned):
        return "month-range"
    if YEAR_RANGE_RE.search(cleaned):
        return "year-range"
    if YEAR_ONLY_RE.match(cleaned):
        return "year"
    return "other"


def _collect_periods(data: ScoringInput) -> list[str]:
    periods: list[str] = []
    for collection in (data.education, data.experience, data.projects):
        for item in collection:
            period = str(item.get("period") or "").strip()
            if period:
                periods.append(period)
    return periods


def score_format_length(
    data: ScoringInput,
) -> tuple[int, int, list[str]]:
    score = 0
    reasons: list[str] = []
    text = data.raw_text or ""

    if not text.strip():
        pages = 0
        page_note = "Tidak ada teks untuk mengukur panjang"
    elif data.page_count is not None:
        pages = max(1, data.page_count)
        page_note = f"{pages} halaman"
    else:
        words = len(text.split())
        pages = max(1, math.ceil(words / WORDS_PER_PAGE))
        page_note = f"sekitar {pages} halaman (perkiraan dari jumlah kata)"

    if pages == 0:
        page_points = 0
    elif 1 <= pages <= 2:
        page_points = FORMAT_PAGE_MAX
    elif pages == 3:
        page_points = 4
    else:
        page_points = 2
    score += page_points
    reasons.append(
        f"Panjang: {page_note} (+{page_points}/{FORMAT_PAGE_MAX})"
    )

    links = data.links or {}
    if (links.get("github") or "").strip():
        score += 2
        reasons.append("Link GitHub tersedia (+2/2)")
    else:
        reasons.append("Link GitHub belum ada (0/2)")

    if (links.get("linkedin") or "").strip():
        score += 2
        reasons.append("Link LinkedIn tersedia (+2/2)")
    else:
        reasons.append("Link LinkedIn belum ada (0/2)")

    periods = _collect_periods(data)
    styles = {_date_style(period) for period in periods}
    if not periods:
        date_points = 0
        date_reason = (
            "Belum ada periode tanggal pada pendidikan/pengalaman/proyek"
        )
    elif len(periods) == 1:
        date_points = 2
        date_reason = (
            "Hanya ada satu periode; konsistensi belum bisa dinilai"
        )
    elif len(styles) == 1 and "other" not in styles:
        date_points = FORMAT_DATE_MAX
        date_reason = f"Format tanggal konsisten ({len(periods)} periode)"
    else:
        date_points = 2
        date_reason = "Format tanggal tidak konsisten antar entri"
    score += date_points
    reasons.append(f"{date_reason} (+{date_points}/{FORMAT_DATE_MAX})")

    return score, FORMAT_CRITERIA_MAX, reasons


CRITERIA = (
    (
        "section_completeness",
        "Kelengkapan section",
        score_section_completeness,
        SECTION_CRITERIA_MAX,
    ),
    (
        "description_quality",
        "Kualitas deskripsi",
        score_description_quality,
        DESCRIPTION_CRITERIA_MAX,
    ),
    (
        "ats_readability",
        "Keterbacaan ATS",
        score_ats_readability,
        ATS_CRITERIA_MAX,
    ),
    (
        "skills_relevance",
        "Skill dan relevansi",
        score_skills_relevance,
        SKILLS_CRITERIA_MAX,
    ),
    (
        "format_length",
        "Format dan panjang",
        score_format_length,
        FORMAT_CRITERIA_MAX,
    ),
)

TOTAL_MAX_SCORE = sum(item[3] for item in CRITERIA)
assert TOTAL_MAX_SCORE == 100


def score_cv(data: ScoringInput) -> ScoreResult:
    criteria: list[CriterionResult] = []
    for key, label, scorer, max_score in CRITERIA:
        score, declared_max, reasons = scorer(data)
        score = max(0, min(score, declared_max))
        criteria.append(
            CriterionResult(
                key=key,
                label=label,
                score=score,
                max_score=declared_max,
                reasons=reasons,
            )
        )

    total = sum(criterion.score for criterion in criteria)
    return ScoreResult(total_score=total, criteria=criteria)
