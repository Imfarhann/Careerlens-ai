import re
from functools import lru_cache
from typing import Any

from app.services.skills_catalog import (
    category_rank,
    load_skills,
    normalize_skill_name,
)

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        "ringkasan",
        "ringkasan profil",
        "profil",
        "tentang saya",
        "summary",
        "profile",
        "professional summary",
        "about",
        "about me",
        "objective",
        "career objective",
        "tujuan",
    ),
    "education": (
        "pendidikan",
        "riwayat pendidikan",
        "pendidikan formal",
        "education",
        "academic background",
        "academics",
        "educational background",
        "education history",
    ),
    "experience": (
        "pengalaman",
        "pengalaman kerja",
        "riwayat pekerjaan",
        "pengalaman profesional",
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
        "career history",
    ),
    "projects": (
        "proyek",
        "projek",
        "proyek pribadi",
        "proyek unggulan",
        "projects",
        "personal projects",
        "selected projects",
        "portfolio",
        "portofolio",
    ),
    "skills": (
        "keahlian",
        "keterampilan",
        "skill",
        "skills",
        "kompetensi",
        "technical skills",
        "technology stack",
        "tech stack",
        "hard skills",
        "soft skills",
    ),
    "certifications": (
        "sertifikasi",
        "sertifikat",
        "certifications",
        "certificates",
        "licenses",
        "lisensi",
    ),
    "languages": (
        "bahasa",
        "bahasa yang dikuasai",
        "languages",
        "language",
    ),
    "awards": (
        "penghargaan",
        "prestasi",
        "awards",
        "achievements",
        "achievement",
        "honors",
    ),
    "organizations": (
        "organisasi",
        "pengalaman organisasi",
        "organizations",
        "organisation",
        "leadership",
        "volunteer",
        "kegiatan",
        "extracurricular",
    ),
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[A-Za-z0-9_%\-./]+",
    re.IGNORECASE,
)
GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_.\-/]+",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
PHONE_ID_RE = re.compile(
    r"(?<!\d)(?:\+62|62|0)8[\s.\-]?(?:\d[\s.\-]?){6,11}\d(?!\d)"
)
PHONE_INTL_RE = re.compile(
    r"(?<!\d)\+[1-9]\d{0,2}[\s.\-]?(?:\(\d{2,4}\)|\d{2,4})[\s.\-]"
    r"\d{3,4}[\s.\-]?\d{3,4}(?!\d)"
)
BULLET_RE = re.compile(r"^(?:[-*•●▪◦‣]|\d+[.)])\s+")
MONTH = r"(?:jan|feb|mar|apr|may|mei|jun|jul|aug|agu|sep|oct|okt|nov|dec|des)[a-z]*\.?"
PERIOD_RE = re.compile(
    rf"(?:{MONTH}\s*)?(?:19|20)\d{{2}}\s*"
    rf"(?:-|–|—|to|until|sampai|hingga|s\.?d\.?)\s*"
    rf"(?:(?:{MONTH}\s*)?(?:19|20)\d{{2}}|sekarang|present|now|current)",
    re.IGNORECASE,
)
YEAR_ONLY_RE = re.compile(r"^(?:19|20)\d{2}$")
PAREN_YEAR_RE = re.compile(r"[\(\[]((?:19|20)\d{2})[\)\]]")
NAME_TOKEN_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ.'\-]*$")
SKIP_NAME_LINES = {
    "curriculum vitae",
    "curriculum vitae (cv)",
    "resume",
    "daftar riwayat hidup",
    "cv",
}


def _normalize_heading(value: str) -> str:
    return " ".join(value.split()).casefold()


@lru_cache
def _heading_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for section, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            index[_normalize_heading(alias)] = section
    return index


def match_heading(line: str) -> tuple[str, str] | None:
    cleaned = line.strip().strip("*#").strip()
    if not cleaned:
        return None

    if len(cleaned) <= 80:
        candidate = cleaned.rstrip(":").strip()
        key = _normalize_heading(candidate)
        if key in _heading_index() and len(key.split()) <= 5:
            return _heading_index()[key], ""

    for separator in (":", " | "):
        if separator not in cleaned:
            continue
        head, rest = cleaned.split(separator, 1)
        head_key = _normalize_heading(head)
        rest = rest.strip()
        if (
            rest
            and len(head) <= 80
            and head_key in _heading_index()
            and len(head_key.split()) <= 5
        ):
            return _heading_index()[head_key], rest

    return None


def split_sections(text: str) -> tuple[list[str], dict[str, list[str]]]:
    preamble: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current is not None:
                sections[current].append("")
            continue

        heading = match_heading(line)
        if heading is not None:
            current, inline = heading
            sections.setdefault(current, [])
            if inline:
                sections[current].append(inline)
            continue

        if current is None:
            preamble.append(line)
        else:
            sections[current].append(line)

    for key, lines in sections.items():
        while lines and not lines[-1]:
            lines.pop()

    return preamble, sections


def extract_email(text: str) -> str | None:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def extract_phone(text: str) -> str | None:
    candidates: list[tuple[int, str]] = []
    for pattern in (PHONE_ID_RE, PHONE_INTL_RE):
        for match in pattern.finditer(text):
            raw = match.group(0).strip(" .-")
            digit_count = len(_digits(raw))
            if 9 <= digit_count <= 15:
                candidates.append((match.start(), raw))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _normalize_url(value: str) -> str:
    url = value.strip().strip(".,;:)]>")
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = f"https://{url}"
    return url


def extract_links(text: str) -> dict[str, Any]:
    github_match = GITHUB_RE.search(text)
    linkedin_match = LINKEDIN_RE.search(text)

    found = [match.group(0) for match in URL_RE.finditer(text)]
    other: list[str] = []
    for url in found:
        normalized = _normalize_url(url)
        lowered = normalized.lower()
        if "github.com" in lowered or "linkedin.com" in lowered:
            continue
        if normalized not in other:
            other.append(normalized)

    return {
        "github": _normalize_url(github_match.group(0)) if github_match else None,
        "linkedin": (
            _normalize_url(linkedin_match.group(0)) if linkedin_match else None
        ),
        "other": other[:5],
    }


def extract_name(lines: list[str]) -> str | None:
    for raw_line in lines[:15]:
        line = raw_line.strip()
        if not line or len(line) > 60:
            continue
        lowered = line.casefold()
        if lowered in SKIP_NAME_LINES:
            continue
        if any(marker in lowered for marker in ("@", "http", "www.", "|", ":")):
            continue
        if re.search(r"\d", line):
            continue
        if match_heading(line) is not None:
            continue

        words = line.split()
        if 2 <= len(words) <= 4 and all(NAME_TOKEN_RE.match(word) for word in words):
            return line

    return None


def _clean_period_line(line: str) -> tuple[str, str]:
    if YEAR_ONLY_RE.match(line):
        return line, ""

    match = PERIOD_RE.search(line) or PAREN_YEAR_RE.search(line)
    if not match:
        return "", line

    period = match.group(0).strip().strip("()[]")
    remainder = (line[: match.start()] + " " + line[match.end() :]).strip()
    remainder = remainder.strip(" .,;|/-–—")
    remainder = re.sub(r"\(\s*\)|\[\s*\]", "", remainder).strip(" .,;|/-–—")
    remainder = re.sub(r"\s{2,}", " ", remainder)
    return period, remainder


def _parse_block(block: list[str]) -> tuple[str, list[str], list[str]]:
    period = ""
    body: list[str] = []
    details: list[str] = []

    for raw_line in block:
        line = raw_line.strip()
        if not line:
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            details.append(BULLET_RE.sub("", line).strip())
            continue

        found_period, remainder = _clean_period_line(line)
        if found_period and not period:
            period = found_period
        if remainder:
            body.append(remainder)

    return period, body, details


def split_entries(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)

    if current:
        blocks.append(current)
    return blocks


def parse_education(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for block in split_entries(lines):
        period, body, details = _parse_block(block)
        institution = body[0] if body else ""
        degree = body[1] if len(body) > 1 else ""
        if not institution and not degree:
            continue
        entries.append(
            {
                "institution": institution,
                "degree": degree,
                "period": period,
                "details": [*details, *body[2:]],
            }
        )
    return entries


def parse_experience(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for block in split_entries(lines):
        period, body, details = _parse_block(block)
        role = body[0] if body else ""
        company = body[1] if len(body) > 1 else ""
        if not role and not company:
            continue
        entries.append(
            {
                "role": role,
                "company": company,
                "period": period,
                "details": [*details, *body[2:]],
            }
        )
    return entries


def parse_projects(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for block in split_entries(lines):
        period, body, details = _parse_block(block)
        name = body[0] if body else ""
        if not name:
            continue
        description_lines = [*body[1:], *[f"- {detail}" for detail in details]]
        entries.append(
            {
                "name": name,
                "period": period,
                "description": "\n".join(description_lines).strip(),
            }
        )
    return entries


def _section_text(sections: dict[str, list[str]], key: str) -> str | None:
    lines = [line for line in sections.get(key, []) if line.strip()]
    return "\n".join(lines).strip() if lines else None


@lru_cache
def _skill_patterns() -> tuple[tuple[re.Pattern[str], dict[str, Any], int], ...]:
    patterns: list[tuple[re.Pattern[str], dict[str, Any], int]] = []
    for skill in load_skills():
        tokens = {skill["name"], *skill.get("aliases", [])}
        for token in tokens:
            escaped = re.escape(token)
            flags = 0 if len(token.strip()) <= 2 else re.IGNORECASE
            pattern = re.compile(
                r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])",
                flags,
            )
            patterns.append((pattern, skill, len(token)))
    return tuple(patterns)


def extract_skills(text: str) -> list[dict[str, str]]:
    matches: list[tuple[int, int, dict[str, Any]]] = []
    for pattern, skill, _ in _skill_patterns():
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), skill))

    matches.sort(key=lambda item: (-(item[1] - item[0]), item[0]))

    accepted: list[tuple[int, int, dict[str, Any]]] = []
    for start, end, skill in matches:
        if any(start < taken_end and end > taken_start for taken_start, taken_end, _ in accepted):
            continue
        accepted.append((start, end, skill))

    unique = {skill["name"]: skill for _, _, skill in accepted}
    ordered = sorted(
        unique.values(),
        key=lambda skill: (category_rank(skill["category"]), skill["name"].casefold()),
    )
    return [
        {"name": skill["name"], "category": skill["category"]} for skill in ordered
    ]


def extract_profile(text: str) -> dict[str, Any]:
    preamble, sections = split_sections(text)
    name_lines = preamble if preamble else text.splitlines()

    extra: dict[str, list[str]] = {}
    for key in ("certifications", "languages", "awards", "organizations"):
        lines = [line for line in sections.get(key, []) if line.strip()]
        if lines:
            extra[key] = lines

    return {
        "name": extract_name(name_lines),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "summary": _section_text(sections, "summary"),
        "links": extract_links(text),
        "education": parse_education(sections.get("education", [])),
        "experience": parse_experience(sections.get("experience", [])),
        "projects": parse_projects(sections.get("projects", [])),
        "skills": extract_skills(text),
        "extra": extra,
    }
