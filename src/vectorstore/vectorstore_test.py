# import json
# from src.vectorstore.qdrant_store import QdrantVectorStore

# # Instantiate your vector store
# qdrant_store = QdrantVectorStore()

# # Define a query
# query = "Huber Loss for HistGradientBoostingRegressor"

# # Run search
# results = qdrant_store.search_similar_issues(query_text=query)

# # Print results
# print("\nTop similar issues:")
# for i, hit in enumerate(results, start=1):
#     print(f"\nResult {i}:")
#     print(f"Score: {hit.score}")
#     print("Payload:")
#     print(json.dumps(hit.payload, indent=2))


import asyncio

from src.vectorstore.qdrant_store_async import AsyncQdrantVectorStore


async def main() -> None:
    async_qdrant_vector_store = AsyncQdrantVectorStore()
    query = "Huber Loss for HistGradientBoostingRegressor"

    results = await async_qdrant_vector_store.search_similar_issues(query_text=query)
    for i, hit in enumerate(results, start=1):
        print(f"Result {i}:")
        print(f"Score: {hit.score}")
        print("Payload:")
        print(hit.payload)


if __name__ == "__main__":
    asyncio.run(main())
