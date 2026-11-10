import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "skills.json"

CATEGORY_ORDER = (
    "Programming",
    "Web",
    "Database",
    "Data/ML",
    "DevOps",
    "Tools",
    "Soft Skill",
)


def normalize_skill_name(value: str) -> str:
    return " ".join(value.split()).casefold()


@lru_cache
def load_skills() -> tuple[dict[str, Any], ...]:
    with DATA_FILE.open(encoding="utf-8") as handle:
        return tuple(json.load(handle))


@lru_cache
def alias_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for skill in load_skills():
        for token in [skill["name"], *skill.get("aliases", [])]:
            index[normalize_skill_name(token)] = skill
    return index


def find_skill(name: str) -> dict[str, Any] | None:
    return alias_index().get(normalize_skill_name(name))


def category_rank(category: str) -> int:
    try:
        return CATEGORY_ORDER.index(category)
    except ValueError:
        return len(CATEGORY_ORDER)
