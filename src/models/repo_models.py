import yaml
from pydantic import BaseModel, Field

from src.utils.config import settings


class RepoConfig(BaseModel):
    owner: str
    repo: str
    state: str = Field(default="all")
    per_page: int = Field(default=50, ge=1, le=100)
    max_pages: int = Field(default=2, ge=1)


def load_repositories_from_yaml(path: str) -> list[RepoConfig]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return [RepoConfig(**repo) for repo in data]


repositories = load_repositories_from_yaml(settings.REPOS_CONFIG)
