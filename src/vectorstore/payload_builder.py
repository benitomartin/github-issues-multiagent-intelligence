from src.models.db_models import Comment, Issue
from src.utils.config import settings


def build_comment_payload(comment: Comment, issue: Issue) -> dict:
    return {
        "issue_number": issue.number,
        "repo": issue.repo,
        "owner": issue.owner,
        "chunk_text": "",  # Fill this dynamically in ingestion
        "comment_id": comment.comment_id,
        "url": issue.url or "",
        "title": issue.title,
        "is_bug": issue.is_bug,
        "is_feature": issue.is_feature,
        "comment_author": comment.author or "",
        "comment_created_at": comment.created_at.isoformat() if comment.created_at else None,
        "comment_updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        "issue_state": issue.state or "",
        "issue_created_at": issue.created_at.isoformat() if issue.created_at else None,
        "issue_updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
    }


CHUNK_SIZE = settings.CHUNK_SIZE
BATCH_SIZE = settings.BATCH_SIZE
CONCURRENT_COMMENTS = settings.CONCURRENT_COMMENTS
