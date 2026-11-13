"""CV profile and API schemas.

`ExtractedProfile` is the schema Claude must fill (structured outputs): every field is required
and nullable so the model can say "not in the CV" explicitly instead of inventing a value.
`CvProfile` is the same shape with defaults, used for user edits and API responses.
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Profile (shared by AI output and user edits) ───────────────────────


class Language(BaseModel):
    name: str = Field(max_length=60)
    level: str | None = Field(default=None, max_length=60)


class Experience(BaseModel):
    title: str = Field(max_length=150)
    company: str | None = Field(default=None, max_length=150)
    location: str | None = Field(default=None, max_length=150)
    start_date: str | None = Field(default=None, max_length=20, description="YYYY-MM or YYYY")
    end_date: str | None = Field(default=None, max_length=20, description="YYYY-MM, YYYY or null")
    is_current: bool = False
    description: str | None = Field(default=None, max_length=3000)


class Education(BaseModel):
    degree: str = Field(max_length=200)
    institution: str | None = Field(default=None, max_length=200)
    start_date: str | None = Field(default=None, max_length=20)
    end_date: str | None = Field(default=None, max_length=20)


class CvProfile(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)
    headline: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=3000)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=150)
    links: list[str] = Field(default_factory=list, max_length=20)
    total_years_experience: float | None = Field(default=None, ge=0, le=70)
    skills: list[str] = Field(default_factory=list, max_length=100)
    languages: list[Language] = Field(default_factory=list, max_length=20)
    experience: list[Experience] = Field(default_factory=list, max_length=40)
    education: list[Education] = Field(default_factory=list, max_length=20)
    certifications: list[str] = Field(default_factory=list, max_length=40)


class ExtractedLanguage(BaseModel):
    name: str
    level: str | None


class ExtractedExperience(BaseModel):
    title: str
    company: str | None
    location: str | None
    start_date: str | None
    end_date: str | None
    is_current: bool
    description: str | None


class ExtractedEducation(BaseModel):
    degree: str
    institution: str | None
    start_date: str | None
    end_date: str | None


class ExtractedProfile(BaseModel):
    """Output contract for the extraction prompt (all keys required; null = not present)."""

    full_name: str | None
    headline: str | None
    summary: str | None
    email: str | None
    phone: str | None
    location: str | None
    links: list[str]
    total_years_experience: float | None
    skills: list[str]
    languages: list[ExtractedLanguage]
    experience: list[ExtractedExperience]
    education: list[ExtractedEducation]
    certifications: list[str]


# ── API ────────────────────────────────────────────────────────────────

Origin = Literal["upload", "linkedin_pdf"]


class CvSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    origin: str
    is_primary: bool
    archived: bool
    extraction_status: str
    created_at: datetime
    updated_at: datetime


class CvOut(CvSummaryOut):
    profile: CvProfile
    extraction_notes: dict[str, Any]
    has_source_text: bool


class CvBlankIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CvPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_primary: Literal[True] | None = None
    archived: bool | None = None


class PreferencesData(BaseModel):
    roles: list[str] = Field(default_factory=list, max_length=10)
    locations: list[str] = Field(default_factory=list, max_length=10)
    remote: Literal["any", "remote", "hybrid", "onsite"] = "any"
    min_salary: int | None = Field(default=None, ge=0, le=1_000_000)
    sources: list[str] = Field(default_factory=list, max_length=20)
