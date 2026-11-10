from collections import Counter

from app.services.skills_catalog import (
    CATEGORY_ORDER,
    alias_index,
    find_skill,
    load_skills,
)


def test_catalog_has_expected_size_and_categories():
    skills = load_skills()
    categories = Counter(skill["category"] for skill in skills)

    assert 140 <= len(skills) <= 170
    assert set(categories) == set(CATEGORY_ORDER)


def test_catalog_names_and_aliases_are_unique():
    skills = load_skills()
    names = [skill["name"] for skill in skills]
    tokens = [
        token
        for skill in skills
        for token in [skill["name"], *skill.get("aliases", [])]
    ]

    assert len(names) == len(set(names))
    normalized = [" ".join(token.split()).casefold() for token in tokens]
    assert len(normalized) == len(set(normalized))


def test_alias_lookup_returns_canonical_skill():
    assert find_skill("js")["name"] == "JavaScript"
    assert find_skill("Postgres")["name"] == "PostgreSQL"
    assert find_skill("k8s")["name"] == "Kubernetes"
    assert find_skill("Komunikasi")["name"] == "Communication"


def test_alias_index_covers_every_skill():
    index = alias_index()

    for skill in load_skills():
        assert " ".join(skill["name"].split()).casefold() in index
