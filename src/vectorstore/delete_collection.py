import asyncio

from src.vectorstore.qdrant_store import AsyncQdrantVectorStore


async def main() -> None:
    vectorstore = AsyncQdrantVectorStore()
    await vectorstore.delete_collection()


if __name__ == "__main__":
    asyncio.run(main())
