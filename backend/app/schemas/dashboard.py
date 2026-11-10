import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.analysis import ScoreBreakdown, SuggestionsRead
from app.schemas.jobs import SkillGapItemRead


class AnalysisHistoryItemRead(BaseModel):
    id: uuid.UUID
    cv_id: uuid.UUID
    original_filename: str
    created_at: datetime
    total_score: int


class AnalysisHistoryRead(BaseModel):
    analyses: list[AnalysisHistoryItemRead] = Field(default_factory=list)


class CriterionComparisonRead(BaseModel):
    key: str
    label: str
    base_score: int
    compare_score: int
    delta: int
    max_score: int


class AnalysisCompareRead(BaseModel):
    base_analysis_id: uuid.UUID
    compare_analysis_id: uuid.UUID
    base_total_score: int
    compare_total_score: int
    total_score_delta: int
    criteria: list[CriterionComparisonRead] = Field(default_factory=list)
    skills_added: list[str] = Field(default_factory=list)
    skills_removed: list[str] = Field(default_factory=list)


class DashboardMatchRead(BaseModel):
    job_id: uuid.UUID
    slug: str
    title: str
    company: str
    level: str
    match_percentage: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class SkillCategoryCountRead(BaseModel):
    category: str
    count: int


class CategoryCoverageRead(BaseModel):
    category: str
    owned: int
    total: int
    percentage: float


class DashboardRead(BaseModel):
    analysis_id: uuid.UUID
    created_at: datetime
    total_score: int
    score_breakdown: ScoreBreakdown
    skill_by_category: list[SkillCategoryCountRead] = Field(
        default_factory=list
    )
    category_coverage: list[CategoryCoverageRead] = Field(
        default_factory=list
    )
    top_matches: list[DashboardMatchRead] = Field(default_factory=list)
    top_gaps: list[SkillGapItemRead] = Field(default_factory=list)
    suggestions: SuggestionsRead
