from typing import Any, TypedDict

from pydantic import BaseModel, Field


class ClassificationState(TypedDict, total=False):
    category: str
    priority: str
    labels: list[str]
    assignee: str


class Recommendation(TypedDict, total=False):
    summary: str
    references: list[str]


class IssueState(TypedDict, total=False):
    title: str
    body: str
    similar_issues: list[dict[str, Any]]
    classification: ClassificationState
    recommendation: Recommendation
    errors: list[str]


class ResponseFormatter(BaseModel):
    """Pydantic schema to enforce structured LLM output."""

    category: str = Field(description="The category of the issue")
    priority: str = Field(description="The priority of the issue")
    labels: list[str] = Field(description="The labels of the issue")
    assignee: str = Field(description="The assignee of the issue")
    errors: list[str] = Field(description="The errors of the issue")
