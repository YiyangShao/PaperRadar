"""Unified Pydantic models for normalized OpenReview data (v1 + v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Paper(BaseModel):
    forum_id: str
    raw_id: str
    venue: str
    api_version: str
    title: str
    abstract: str
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    primary_area: str | None = None
    pdf_url: str | None = None
    is_withdrawn: bool = False


class Review(BaseModel):
    review_id: str
    forum_id: str
    venue: str
    api_version: str
    reviewer_handle: str

    rating: int | None = None
    confidence: int | None = None

    summary: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    questions: str | None = None
    overall_verdict: str | None = None

    soundness: int | None = None
    presentation: int | None = None
    contribution: int | None = None

    correctness: int | None = None
    technical_novelty: int | None = None
    empirical_novelty: int | None = None

    review_text: str

    raw_content: dict


class MetaReview(BaseModel):
    meta_id: str
    forum_id: str
    venue: str
    api_version: str

    metareview: str | None = None
    decision: str | None = None
    why_not_higher: str | None = None
    why_not_lower: str | None = None

    raw_content: dict
