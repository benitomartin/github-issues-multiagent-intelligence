# src/models/github_models.py


from pydantic import BaseModel


class GitHubLabel(BaseModel):
    name: str


class GitHubUser(BaseModel):
    login: str


class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str | None
    state: str
    user: GitHubUser
    html_url: str
    created_at: str
    updated_at: str
    labels: list[GitHubLabel] | None = []


class GitHubComment(BaseModel):
    id: int
    user: GitHubUser
    body: str
    created_at: str | None
    updated_at: str | None
