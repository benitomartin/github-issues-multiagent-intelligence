import asyncio
import textwrap
import uuid
from collections.abc import AsyncGenerator, Generator, Iterable
from typing import Any

from loguru import logger
from qdrant_client.models import Batch, FieldCondition, Filter, MatchValue

from src.database.session import db
from src.models.db_models import Comment, Issue
from src.vectorstore.payload_builder import BATCH_SIZE, CHUNK_SIZE, CONCURRENT_COMMENTS, build_comment_payload
from src.vectorstore.qdrant_store import AsyncQdrantVectorStore


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


async def comment_already_ingested(qdrant: AsyncQdrantVectorStore, issue_number: int, comment_id: int) -> bool:
    points, _ = await qdrant.client.scroll(
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


async def chunk_data_for_comment(
    comment: Comment, issue: Issue, qdrant: AsyncQdrantVectorStore
) -> AsyncGenerator[dict, None]:
    chunks = split_text_into_chunks(comment.body or "")
    for chunk in chunks:
        dense = await qdrant.dense_vectors([chunk])
        sparse = await qdrant.sparse_vectors([chunk])
        payload = build_comment_payload(comment, issue)
        payload["chunk_text"] = chunk

        yield {
            "id": uuid.uuid4().hex,
            "dense": dense[0],
            "sparse": sparse[0].as_dict() if hasattr(sparse[0], "as_dict") else sparse[0],
            "payload": payload,
        }


async def upsert_comment_chunks(qdrant: AsyncQdrantVectorStore, comment: Comment, issue: Issue) -> bool:
    if not comment.body:
        logger.info(f"Skipping empty comment {comment.comment_id} in issue #{issue.number}")
        return False

    if await comment_already_ingested(qdrant, int(issue.number), comment.comment_id):
        logger.info(f"Skipping comment {comment.comment_id} in issue #{issue.number} — already ingested.")
        return False

    chunk_gen = chunk_data_for_comment(comment, issue, qdrant)
    batches_for_comment = 0

    async for batch in async_batch_iterable(chunk_gen, batch_size=BATCH_SIZE):
        ids = [item["id"] for item in batch]
        dense_vectors = [item["dense"] for item in batch]
        sparse_vectors = [item["sparse"] for item in batch]
        payloads = [item["payload"] for item in batch]

        try:
            await qdrant.client.upsert(
                collection_name=qdrant.collection_name,
                points=Batch(
                    ids=ids,
                    payloads=payloads,
                    vectors={"dense": dense_vectors, "miniCOIL": sparse_vectors},
                ),
            )
            batches_for_comment += 1
        except Exception as upsert_error:
            logger.error(f"Failed to upsert comment {comment.comment_id}: {upsert_error}")

    if batches_for_comment > 0:
        logger.info(f"Upserted {batches_for_comment} batch(es) for comment {comment.comment_id} in issue #{issue.number}")
        return True
    return False


async def async_batch_iterable(
    aiterable: AsyncGenerator[Any, None], batch_size: int = BATCH_SIZE
) -> AsyncGenerator[list[Any], None]:
    batch = []
    async for item in aiterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


async def process_issue_comments(qdrant: AsyncQdrantVectorStore, issue: Issue) -> None:
    with db.session_scope() as session:
        comments = session.query(Comment).filter(Comment.issue_id == issue.id).order_by(Comment.created_at.asc()).all()

        semaphore = asyncio.Semaphore(CONCURRENT_COMMENTS)

        async def sem_task(comment: Comment) -> bool:
            async with semaphore:
                return await upsert_comment_chunks(qdrant, comment, issue)

        tasks = [sem_task(comment) for comment in comments if comment.body]
        results = await asyncio.gather(*tasks)

        total_comments = len(comments)
        total_skipped = total_comments - sum(results)
        total_ingested = sum(results)

        logger.info(
            f"Issue #{issue.number} from {issue.repo} processed: "
            f"{total_comments} comments total, "
            f"{total_skipped} skipped, "
            f"{total_ingested} ingested."
        )


async def ingest_issues_to_qdrant_async() -> None:
    qdrant = AsyncQdrantVectorStore()
    with db.session_scope() as session:
        issues = session.query(Issue).yield_per(10)
        for issue in issues:
            await process_issue_comments(qdrant, issue)


if __name__ == "__main__":
    asyncio.run(ingest_issues_to_qdrant_async())
