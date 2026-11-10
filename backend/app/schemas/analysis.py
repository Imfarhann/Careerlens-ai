import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CriterionRead(BaseModel):
    key: str
    label: str
    score: int
    max_score: int
    reasons: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    version: int = 1
    total_score: int
    criteria: list[CriterionRead] = Field(default_factory=list)


class SuggestionsRead(BaseModel):
    items: list[str] = Field(default_factory=list)
    source: str = "fallback"


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cv_id: uuid.UUID
    total_score: int
    score_breakdown: ScoreBreakdown
    suggestions: SuggestionsRead
    created_at: datetime
