import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    period: str = ""
    details: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    role: str = ""
    company: str = ""
    period: str = ""
    details: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str = ""
    period: str = ""
    description: str = ""


class LinkSet(BaseModel):
    github: str | None = None
    linkedin: str | None = None
    other: list[str] = Field(default_factory=list)

    @field_validator("github", "linkedin", mode="before")
    @classmethod
    def empty_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=40)

    @field_validator("name", "category", mode="before")
    @classmethod
    def strip_values(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cv_id: uuid.UUID
    original_filename: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    links: LinkSet = Field(default_factory=LinkSet)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
    skills: list[SkillRead] = Field(default_factory=list)
    updated_at: datetime


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    summary: str | None = None
    links: LinkSet | None = None
    education: list[EducationEntry] | None = None
    experience: list[ExperienceEntry] | None = None
    projects: list[ProjectEntry] | None = None
    skills: list[SkillInput] | None = None

    @field_validator("email", mode="before")
    @classmethod
    def blank_email_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("name", "phone", mode="before")
    @classmethod
    def empty_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value
