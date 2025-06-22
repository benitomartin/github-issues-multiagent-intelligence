from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
@patch("src.vectorstore.qdrant_store.AsyncQdrantVectorStore", autospec=True)
async def test_create_collection_called(MockVectorStore: MagicMock) -> None:
    mock_instance = MockVectorStore.return_value
    mock_instance.create_collection = AsyncMock()

    vectorstore = mock_instance
    await vectorstore.create_collection()

    mock_instance.create_collection.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.vectorstore.qdrant_store.AsyncQdrantVectorStore", autospec=True)
async def test_delete_collection_called(MockVectorStore: MagicMock) -> None:
    mock_instance = MockVectorStore.return_value
    mock_instance.delete_collection = AsyncMock()

    vectorstore = mock_instance
    await vectorstore.delete_collection()

    mock_instance.delete_collection.assert_awaited_once()
