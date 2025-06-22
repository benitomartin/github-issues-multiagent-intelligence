import pytest

from src.vectorstore.qdrant_store import AsyncQdrantVectorStore


@pytest.mark.asyncio
async def test_search_similar_issues_returns_results() -> None:
    vectorstore = AsyncQdrantVectorStore()
    query = "Unjustified number of unique classes > 50% warning in CalibratedClassifierCV"

    results = await vectorstore.search_similar_issues(query_text=query)

    # Basic assertion: ensure results are returned (if your collection is populated)
    assert isinstance(results, list)
    assert len(results) > 0

    if results:
        first_result = results[0]
        assert hasattr(first_result, "score")
        assert hasattr(first_result, "payload")
