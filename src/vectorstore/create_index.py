import asyncio

from src.vectorstore.qdrant_store import AsyncQdrantVectorStore


async def main() -> None:
    vectorstore = AsyncQdrantVectorStore()
    await vectorstore.create_indexes()


if __name__ == "__main__":
    asyncio.run(main())
