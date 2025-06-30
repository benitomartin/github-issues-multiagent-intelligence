import time
from datetime import UTC, datetime

import requests
from loguru import logger
from sqlalchemy.orm import Session

from src.database.session import DB
from src.models.db_models import Comment, Issue
from src.models.github_models import GitHubComment, GitHubIssue


class GitHubIssuesCollector:
    def __init__(self, db: DB, token: str | None = None):
        self.db = db
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DocuMind-Agent/1.0",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

    def parse_github_datetime(self, iso_str: str | None) -> datetime | None:
        if not iso_str:
            return None
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.astimezone(UTC).replace(tzinfo=None, microsecond=0)
        except Exception:
            return None

    def get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        labels: str | None = None,
        per_page: int = 100,
        max_pages: int = 5,
    ) -> list[GitHubIssue]:
        issues = []
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
                "per_page": str(per_page),
                "page": str(page),
                "sort": "created",
                "direction": "desc",
            }
            if labels:
                params["labels"] = labels

            logger.info(f"Fetching page {page} for {owner}/{repo}...")
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                raw_issues = response.json()
                if not raw_issues:
                    break

                page_issues = []
                for issue_dict in raw_issues:
                    if "pull_request" in issue_dict:
                        continue
                    try:
                        issue = GitHubIssue(**issue_dict)
                        page_issues.append(issue)
                    except Exception as e:
                        logger.error(f"Failed to parse issue: {e}")

                issues.extend(page_issues)

                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                if remaining < 10:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    sleep_time = reset_time - int(time.time()) + 1
                    logger.warning(f"Rate limit low. Sleeping for {sleep_time} seconds...")
                    time.sleep(sleep_time)

                time.sleep(0.5)

            except requests.RequestException as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

        return issues

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> list[GitHubComment]:
        comments = []
        page = 1
        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
            params = {"per_page": "100", "page": str(page)}

            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                raw_comments = response.json()
                if not raw_comments:
                    break

                page_comments = []
                for comment_dict in raw_comments:
                    try:
                        comment = GitHubComment(**comment_dict)
                        page_comments.append(comment)
                    except Exception as e:
                        logger.error(f"Failed to parse comment: {e}")

                comments.extend(page_comments)

                if len(raw_comments) < 100:
                    break

                page += 1
                time.sleep(0.3)

            except requests.RequestException as e:
                logger.error(f"Error fetching comments for issue #{issue_number}: {e}")
                break

        return comments

    def save_issue(self, session: Session, issue: GitHubIssue, owner: str, repo: str) -> Issue | None:
        if not (issue.body and issue.body.strip()):
            return None

        incoming_updated_at = self.parse_github_datetime(issue.updated_at)

        issue_db = session.query(Issue).filter_by(number=issue.number).first()

        if issue_db:
            if issue_db.updated_at == incoming_updated_at:
                logger.info(f"Skipping unchanged issue #{issue.number}")
                return None
            logger.info(f"Updating issue #{issue.number}")
        else:
            issue_db = Issue(number=issue.number)

        issue_db.owner = owner  # type: ignore
        issue_db.repo = repo  # type: ignore
        issue_db.title = issue.title
        issue_db.body = issue.body
        issue_db.state = issue.state
        issue_db.author = issue.user.login
        issue_db.url = issue.html_url
        issue_db.created_at = self.parse_github_datetime(issue.created_at) or issue_db.created_at  # type: ignore
        issue_db.updated_at = incoming_updated_at or issue_db.updated_at  # type: ignore

        labels = [label.name.lower() for label in issue.labels or []]
        issue_db.is_bug = any("bug" in label for label in labels) or False  # type: ignore
        issue_db.is_feature = any(label in labels for label in ["feature", "enhancement"]) or False  # type: ignore

        session.add(issue_db)
        session.flush()  # To get PK for comments

        return issue_db

    def save_comment(self, session: Session, comment: GitHubComment, issue_id: int) -> None:
        incoming_updated_at = self.parse_github_datetime(comment.updated_at)

        comment_db = session.query(Comment).filter_by(comment_id=comment.id).first()

        if comment_db:
            if comment_db.updated_at == incoming_updated_at:
                logger.info(f"Skipping unchanged comment {comment.id}")
                return
            logger.info(f"Updating comment {comment.id}")
        else:
            comment_db = Comment(comment_id=comment.id, issue_id=issue_id)

        comment_db.author = comment.user.login
        comment_db.body = comment.body
        comment_db.created_at = self.parse_github_datetime(comment.created_at) or comment_db.created_at  # type: ignore
        comment_db.updated_at = incoming_updated_at or comment_db.updated_at  # type: ignore
        session.add(comment_db)

    def save_issues_to_db(self, issues: list[GitHubIssue], owner: str, repo: str) -> None:
        session = self.db.get_session()
        try:
            for issue in issues:
                saved_issue = self.save_issue(session, issue, owner, repo)
                if not saved_issue:
                    continue

                comments = self.get_issue_comments(owner, repo, issue.number)
                for comment in comments:
                    self.save_comment(session, comment, int(saved_issue.id))
            session.commit()
            logger.info(f"Saved {len(issues)} issues (with comments) to the database.")
        except Exception as e:
            logger.error(f"Error saving to DB: {e}")
            session.rollback()
        finally:
            session.close()


if __name__ == "__main__":
    from src.models.repo_models import repositories
    from src.utils.config import settings

    db = DB()  # Create DB instance

    GH_TOKEN = settings.GH_TOKEN
    if not GH_TOKEN:
        logger.warning("No GitHub token provided. Rate limits may be low.")

    collector = GitHubIssuesCollector(db=db, token=GH_TOKEN)

    for repo_cfg in repositories:
        logger.info(f"\n{'=' * 50}\nCollecting issues from {repo_cfg.owner}/{repo_cfg.repo}...\n{'=' * 50}")
        raw_issues = collector.get_issues(
            owner=repo_cfg.owner,
            repo=repo_cfg.repo,
            state=repo_cfg.state,
            per_page=repo_cfg.per_page,
            max_pages=repo_cfg.max_pages,
        )
        collector.save_issues_to_db(raw_issues, repo_cfg.owner, repo_cfg.repo)
        time.sleep(2)
