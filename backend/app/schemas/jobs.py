import uuid

from pydantic import BaseModel, Field


class JobMatchRead(BaseModel):
    job_id: uuid.UUID
    slug: str
    title: str
    company: str
    level: str
    description: str
    match_score: float
    match_percentage: float
    skill_coverage: float
    semantic_similarity: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)


class JobMatchesRead(BaseModel):
    analysis_id: uuid.UUID
    matches: list[JobMatchRead] = Field(default_factory=list)


class JobSummaryRead(BaseModel):
    job_id: uuid.UUID
    slug: str
    title: str
    company: str
    level: str
    match_percentage: float


class LearningResourceRead(BaseModel):
    title: str
    url: str


class SkillGapItemRead(BaseModel):
    skill: str
    category: str
    frequency: int
    job_count: int
    resources: list[LearningResourceRead] = Field(default_factory=list)


class SkillGapRead(BaseModel):
    analysis_id: uuid.UUID
    top_jobs: list[JobSummaryRead] = Field(default_factory=list)
    gaps: list[SkillGapItemRead] = Field(default_factory=list)
