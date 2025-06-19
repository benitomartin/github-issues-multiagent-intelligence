import textwrap
import uuid
from collections.abc import Generator, Iterable
from typing import Any, cast

from loguru import logger
from qdrant_client.models import Batch, FieldCondition, Filter, MatchValue

from src.database.session import get_session
from src.models.db_models import Comment, Issue
from src.vectorstore.qdrant_store import QdrantVectorStore

CHUNK_SIZE = 1000  # characters per chunk
BATCH_SIZE = 20  # batch size for embedding and upsert


def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    return textwrap.wrap(text, width=chunk_size, break_long_words=False)


def batch_iterable(iterable: Iterable[Any], batch_size: int = BATCH_SIZE) -> Generator[list[Any], None, None]:
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def comment_already_ingested(qdrant: QdrantVectorStore, issue_number: int, comment_id: int) -> bool:
    points, _ = qdrant.client.scroll(
        collection_name=qdrant.collection_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="issue_number", match=MatchValue(value=issue_number)),
                FieldCondition(key="comment_id", match=MatchValue(value=comment_id)),
            ]
        ),
        limit=1,
    )
    return len(points) > 0


def chunk_data_for_comment(
    comment: Comment, issue: Issue, qdrant: QdrantVectorStore
) -> Generator[dict[str, Any], None, None]:
    chunks = split_text_into_chunks(cast(str, comment.body))
    for _, chunk in enumerate(chunks):
        yield {
            "id": uuid.uuid4().hex,
            "dense": qdrant.dense_vectors([chunk])[0],
            "sparse": qdrant.sparse_vectors([chunk])[0].as_object(),
            "payload": {
                "issue_number": issue.number,
                "repo": issue.repo,
                "owner": issue.owner,
                "chunk_text": chunk,
                "comment_id": comment.comment_id,
                "url": issue.url,
                "title": issue.title,
                "is_bug": issue.is_bug,
                "is_feature": issue.is_feature,
            },
        }


def ingest_issues_to_qdrant() -> None:
    qdrant = QdrantVectorStore()
    session = get_session()

    try:
        issues = session.query(Issue).yield_per(10)

        for issue in issues:
            comments = session.query(Comment).filter(Comment.issue_id == issue.id).order_by(Comment.created_at.asc()).all()

            total_skipped = 0
            total_upserted_comments = 0
            total_batches = 0

            for comment in comments:
                if not comment.body:
                    logger.info(f"Skipping empty comment {comment.comment_id} in issue #{issue.number}")
                    total_skipped += 1
                    continue

                if comment_already_ingested(
                    qdrant=qdrant, issue_number=int(issue.number), comment_id=cast(int, comment.comment_id)
                ):
                    logger.info(f"Skipping comment {comment.comment_id} in issue #{issue.number} — already ingested.")
                    total_skipped += 1
                    continue

                # Chunk and batch upsert each comment's chunks
                chunk_gen = chunk_data_for_comment(comment, issue, qdrant)
                batches_for_comment = 0

                for batch in batch_iterable(chunk_gen, batch_size=BATCH_SIZE):
                    ids = [item["id"] for item in batch]
                    dense_vectors = [item["dense"] for item in batch]
                    sparse_vectors = [item["sparse"] for item in batch]
                    payloads = [item["payload"] for item in batch]

                    try:
                        qdrant.client.upsert(
                            collection_name=qdrant.collection_name,
                            points=Batch(
                                ids=ids,
                                payloads=payloads,
                                vectors={
                                    "dense": dense_vectors,
                                    "miniCOIL": sparse_vectors,
                                },
                            ),
                        )
                        batches_for_comment += 1
                        total_batches += 1
                    except Exception as upsert_error:
                        logger.error(f"Failed to upsert comment {comment.comment_id}: {upsert_error}")

                if batches_for_comment > 0:
                    logger.info(
                        f"Upserted {batches_for_comment} batch(es) for comment {comment.comment_id} in issue #{issue.number}"
                    )
                    total_upserted_comments += batches_for_comment

            logger.info(
                f"Issue #{issue.number} from {issue.repo} processed: "
                f"{len(comments)} comments total, "
                f"{total_skipped} skipped, "
                f"{total_upserted_comments} ingested, "
                f"{total_batches} batches upserted"
            )

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    ingest_issues_to_qdrant()
