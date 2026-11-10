import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Profile, Skill, UserSkill
from app.services.skills_catalog import find_skill


def resolve_skill(
    db: Session, name: str, category: str | None = None
) -> Skill:
    cleaned = " ".join(name.split())
    if not cleaned:
        raise ValueError("Nama skill tidak boleh kosong")

    catalog = find_skill(cleaned)
    aliases: list[str] = []
    if catalog is not None:
        cleaned = catalog["name"]
        category = catalog["category"]
        aliases = list(catalog.get("aliases", []))

    skill = db.scalar(
        select(Skill).where(func.lower(Skill.name) == cleaned.casefold())
    )
    if skill is not None:
        return skill

    skill = Skill(
        name=cleaned,
        category=category or "Other",
        aliases=aliases,
    )
    db.add(skill)
    db.flush()
    return skill


def _attach_skills(
    db: Session, profile_id: uuid.UUID, items: list[dict[str, Any]]
) -> None:
    seen: set[uuid.UUID] = set()
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        skill = resolve_skill(db, name, item.get("category"))
        if skill.id in seen:
            continue
        seen.add(skill.id)
        db.add(UserSkill(profile_id=profile_id, skill_id=skill.id))


def add_profile_skills(
    db: Session, profile: Profile, items: list[dict[str, Any]]
) -> None:
    _attach_skills(db, profile.id, items)
    db.flush()


def replace_profile_skills(
    db: Session, profile: Profile, items: list[dict[str, Any]]
) -> None:
    db.execute(delete(UserSkill).where(UserSkill.profile_id == profile.id))
    db.flush()
    _attach_skills(db, profile.id, items)
    db.flush()
