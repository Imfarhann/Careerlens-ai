import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Job, JobMatch, JobSkill

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

REQUIRED_WEIGHT = 2.0
NICE_TO_HAVE_WEIGHT = 1.0
SKILL_COVERAGE_WEIGHT = 0.6
SEMANTIC_WEIGHT = 0.4


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(
            list(texts),
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in vectors]


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformerEmbedder()
    return _embedder


def set_embedder(embedder: Embedder | None) -> None:
    global _embedder
    _embedder = embedder


@dataclass(frozen=True)
class JobSkillRef:
    skill_id: Any
    name: str
    category: str = ""
    is_required: bool = True


@dataclass(frozen=True)
class JobCandidate:
    job_id: Any
    title: str
    description: str
    skills: tuple[JobSkillRef, ...] = ()
    embedding: tuple[float, ...] | None = None


@dataclass
class MatchResult:
    job_id: Any
    title: str
    match_score: float
    skill_coverage: float
    semantic_similarity: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    missing_refs: list[JobSkillRef] = field(default_factory=list)


@dataclass
class SkillGap:
    skill_id: Any
    skill: str
    category: str
    frequency: int
    job_count: int


def _text_field(entry: Any, key: str) -> str:
    if isinstance(entry, dict):
        value = entry.get(key)
    else:
        value = getattr(entry, key, None)
    return value.strip() if isinstance(value, str) else ""


def build_profile_text(profile: Any) -> str:
    parts: list[str] = []

    skills = getattr(profile, "skills", None)
    if skills is None:
        skills = [
            item.skill
            for item in getattr(profile, "user_skills", [])
            if getattr(item, "skill", None) is not None
        ]
    for skill in skills:
        name = _text_field(skill, "name")
        if name:
            parts.append(name)

    for experience in getattr(profile, "experience", None) or []:
        role = _text_field(experience, "role")
        if role:
            parts.append(role)

    for project in getattr(profile, "projects", None) or []:
        name = _text_field(project, "name")
        if name:
            parts.append(name)
        description = _text_field(project, "description")
        if description:
            parts.append(description)

    return "\n".join(parts)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = math.fsum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(math.fsum(a * a for a in left))
    right_norm = math.sqrt(math.fsum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def clip_similarity(value: float) -> float:
    return max(0.0, min(1.0, value))


def dedupe_job_skills(
    job_skills: Iterable[JobSkillRef],
) -> list[JobSkillRef]:
    unique: dict[Any, JobSkillRef] = {}
    for ref in job_skills:
        current = unique.get(ref.skill_id)
        if current is None or (ref.is_required and not current.is_required):
            unique[ref.skill_id] = ref
    return list(unique.values())


def compute_skill_coverage(
    user_skill_ids: set[Any],
    job_skills: Iterable[JobSkillRef],
) -> tuple[float, list[str], list[str], list[JobSkillRef]]:
    refs = dedupe_job_skills(job_skills)
    total_weight = 0.0
    earned_weight = 0.0
    matched: list[str] = []
    missing: list[JobSkillRef] = []

    for ref in refs:
        weight = (
            REQUIRED_WEIGHT if ref.is_required else NICE_TO_HAVE_WEIGHT
        )
        total_weight += weight
        if ref.skill_id in user_skill_ids:
            earned_weight += weight
            matched.append(ref.name)
        else:
            missing.append(ref)

    if total_weight == 0:
        return 1.0, [], [], []

    coverage = earned_weight / total_weight
    missing_names = [ref.name for ref in missing]
    return coverage, sorted(matched), sorted(missing_names), missing


def combine_score(coverage: float, similarity: float) -> float:
    return round(
        SKILL_COVERAGE_WEIGHT * coverage
        + SEMANTIC_WEIGHT * clip_similarity(similarity),
        6,
    )


def candidate_from_job(job: Job) -> JobCandidate:
    refs = tuple(
        JobSkillRef(
            skill_id=item.skill_id,
            name=item.skill.name,
            category=item.skill.category,
            is_required=item.is_required,
        )
        for item in job.skills
        if item.skill is not None
    )
    embedding = tuple(job.embedding) if job.embedding else None
    return JobCandidate(
        job_id=job.id,
        title=job.title,
        description=job.description,
        skills=refs,
        embedding=embedding,
    )


def ensure_job_embeddings(
    db: Session, jobs: Sequence[Job], embedder: Embedder
) -> None:
    missing = [job for job in jobs if not job.embedding]
    if not missing:
        return
    vectors = embedder.embed([job.description for job in missing])
    if len(vectors) != len(missing):
        raise ValueError("Jumlah embedding tidak sesuai jumlah lowongan")
    for job, vector in zip(missing, vectors):
        job.embedding = [float(value) for value in vector]
    db.commit()


def rank_candidates(
    profile_text: str,
    user_skill_ids: set[Any],
    candidates: Sequence[JobCandidate],
    embedder: Embedder,
) -> list[MatchResult]:
    profile_vector: tuple[float, ...] | None = None
    if profile_text.strip():
        profile_vectors = embedder.embed([profile_text])
        if profile_vectors:
            profile_vector = tuple(
                float(value) for value in profile_vectors[0]
            )

    pending = [
        candidate for candidate in candidates if candidate.embedding is None
    ]
    computed: dict[Any, tuple[float, ...]] = {}
    if pending:
        vectors = embedder.embed(
            [candidate.description for candidate in pending]
        )
        if len(vectors) != len(pending):
            raise ValueError("Jumlah embedding tidak sesuai jumlah lowongan")
        for candidate, vector in zip(pending, vectors):
            computed[candidate.job_id] = tuple(
                float(value) for value in vector
            )

    results: list[MatchResult] = []
    for candidate in candidates:
        coverage, matched, missing_names, missing_refs = (
            compute_skill_coverage(user_skill_ids, candidate.skills)
        )
        job_vector = candidate.embedding or computed.get(candidate.job_id)
        if profile_vector is None or job_vector is None:
            similarity = 0.0
        else:
            similarity = clip_similarity(
                cosine_similarity(profile_vector, job_vector)
            )
        results.append(
            MatchResult(
                job_id=candidate.job_id,
                title=candidate.title,
                match_score=combine_score(coverage, similarity),
                skill_coverage=round(coverage, 6),
                semantic_similarity=round(similarity, 6),
                matched_skills=matched,
                missing_skills=missing_names,
                missing_refs=missing_refs,
            )
        )

    results.sort(
        key=lambda item: (
            -item.match_score,
            item.title.casefold(),
            str(item.job_id),
        )
    )
    return results


def load_jobs(db: Session) -> list[Job]:
    return list(
        db.scalars(
            select(Job)
            .options(
                selectinload(Job.skills).selectinload(JobSkill.skill)
            )
            .order_by(Job.title, Job.slug)
        )
    )


def match_profile(
    db: Session, profile: Any, embedder: Embedder
) -> list[tuple[Job, MatchResult]]:
    jobs = load_jobs(db)
    if not jobs:
        return []

    ensure_job_embeddings(db, jobs, embedder)

    user_skill_ids = {
        item.skill_id for item in getattr(profile, "user_skills", [])
    }
    candidates = [candidate_from_job(job) for job in jobs]
    results = rank_candidates(
        build_profile_text(profile), user_skill_ids, candidates, embedder
    )

    jobs_by_id = {job.id: job for job in jobs}
    return [
        (jobs_by_id[result.job_id], result)
        for result in results
        if result.job_id in jobs_by_id
    ]


def upsert_job_matches(
    db: Session,
    analysis_id: uuid.UUID,
    results: Sequence[MatchResult],
) -> None:
    existing = {
        item.job_id: item
        for item in db.scalars(
            select(JobMatch).where(JobMatch.analysis_id == analysis_id)
        )
    }
    seen: set[Any] = set()

    for result in results:
        seen.add(result.job_id)
        record = existing.get(result.job_id)
        if record is None:
            record = JobMatch(analysis_id=analysis_id, job_id=result.job_id)
            db.add(record)
        record.match_score = result.match_score
        record.skill_coverage = result.skill_coverage
        record.semantic_similarity = result.semantic_similarity
        record.matched_skills = result.matched_skills
        record.missing_skills = result.missing_skills

    for job_id, record in existing.items():
        if job_id not in seen:
            db.delete(record)

    db.commit()


def compute_skill_gaps(
    results: Sequence[MatchResult], top_jobs: int = 10
) -> list[SkillGap]:
    aggregate: dict[Any, dict[str, Any]] = {}

    for result in results[:top_jobs]:
        for ref in result.missing_refs:
            entry = aggregate.setdefault(
                ref.skill_id,
                {
                    "skill": ref.name,
                    "category": ref.category,
                    "frequency": 0,
                    "job_count": 0,
                },
            )
            entry["frequency"] += 1
            if ref.is_required:
                entry["job_count"] += 1

    gaps = [
        SkillGap(
            skill_id=skill_id,
            skill=entry["skill"],
            category=entry["category"],
            frequency=entry["frequency"],
            job_count=entry["job_count"],
        )
        for skill_id, entry in aggregate.items()
    ]
    gaps.sort(
        key=lambda item: (
            -item.frequency,
            -item.job_count,
            item.skill.casefold(),
        )
    )
    return gaps
