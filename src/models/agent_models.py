from typing import Any

from pydantic import BaseModel, Field


class ClassificationState(BaseModel):
    category: str | None = None
    priority: str | None = None
    labels: list[str] | None = None
    assignee: str | None = None


class Recommendation(BaseModel):
    summary: str | None = None
    references: list[str] | None = None


class IssueState(BaseModel):
    title: str | None = None
    body: str | None = None
    similar_issues: list[dict[str, Any]] | None = None
    classification: ClassificationState | None = None
    recommendation: Recommendation | None = None
    errors: list[str] | None = None
    blocked: bool | None = None
    validation_summary: dict[str, Any] | None = None


class ResponseFormatter(BaseModel):
    """Pydantic schema to enforce structured LLM output."""

    category: str = Field(description="The category of the issue")
    priority: str = Field(description="The priority of the issue")
    labels: list[str] = Field(description="The labels of the issue")
    assignee: str = Field(description="The assignee of the issue")
    errors: list[str] = Field(description="The errors of the issue")
