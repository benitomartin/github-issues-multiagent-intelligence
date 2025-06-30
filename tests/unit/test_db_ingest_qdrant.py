from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.data_pipeline.ingest_embeddings import ingest_issues_to_qdrant_async


@pytest.mark.asyncio
@patch("src.database.session.db")
@patch("src.data_pipeline.ingest_embeddings.AsyncQdrantVectorStore")
async def test_ingest_issues(mock_vectorstore_cls: MagicMock, mock_get_session: MagicMock) -> None:
    # Setup mock session and query return values
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # Mock issues query returning a list with one fake issue object
    fake_issue = MagicMock()
    fake_issue.id = 1
    fake_issue.number = 123
    fake_issue.repo = "repo"
    fake_issue.owner = "owner"
    mock_session.query.return_value.yield_per.return_value = [fake_issue]

    # Setup AsyncQdrantVectorStore mock instance
    mock_vectorstore = mock_vectorstore_cls.return_value
    mock_vectorstore.collection_name = "test_collection"
    mock_vectorstore.client.upsert = AsyncMock()
    mock_vectorstore.dense_vectors = AsyncMock(return_value=[[0.1] * 10])
    mock_vectorstore.sparse_vectors = AsyncMock(return_value=[MagicMock(as_object=lambda: {"indices": [], "values": []})])
    mock_vectorstore.client.scroll = AsyncMock(return_value=([], None))

    # Run ingestion
    await ingest_issues_to_qdrant_async()

    # Assert that upsert was called at least once
    assert mock_vectorstore.client.upsert.await_count > 0
