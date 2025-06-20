import asyncio
import time

from fastembed import SparseTextEmbedding, TextEmbedding
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, models

from src.utils.config import settings


class AsyncQdrantVectorStore:
    def __init__(self) -> None:
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

        self.collection_name = f"{settings.APP_ENV}_{settings.COLLECTION_NAME}"
        self.embedding_size = settings.LEN_EMBEDDINGS

        self.dense_model = TextEmbedding(model_name=settings.DENSE_MODEL_NAME)
        self.sparse_model = SparseTextEmbedding(model_name=settings.SPARSE_MODEL_NAME)

        self.quantization_config = models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8,
                quantile=0.99,
                always_ram=True,
            )
        )

        self.sparse_vectors_config = {"miniCOIL": models.SparseVectorParams(modifier=models.Modifier.IDF)}

    async def dense_vectors(self, texts: list[str]) -> list:
        # Run synchronous embedding in thread pool
        return await asyncio.to_thread(lambda: list(self.dense_model.embed(texts)))

    async def sparse_vectors(self, texts: list[str]) -> list:
        return await asyncio.to_thread(lambda: list(self.sparse_model.embed(texts)))

    async def create_collection(self) -> None:
        exists = await self.client.collection_exists(self.collection_name)
        if exists:
            logger.info(f"Collection '{self.collection_name}' already exists.")
            return

        start = time.time()
        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": models.VectorParams(size=self.embedding_size, distance=Distance.COSINE)},
            quantization_config=self.quantization_config,
            sparse_vectors_config=self.sparse_vectors_config,
        )
        logger.info(f"Collection '{self.collection_name}' created in {time.time() - start:.2f}s.")

    async def delete_collection(self) -> None:
        exists = await self.client.collection_exists(self.collection_name)
        if exists:
            await self.client.delete_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' deleted.")

    async def create_indexes(self) -> None:
        try:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="issue_number",
                field_schema=PayloadSchemaType.INTEGER,
            )
        except Exception as e:
            logger.info(f"Index for 'issue_number' may already exist or failed: {e}")

        try:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="comment_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
        except Exception as e:
            logger.info(f"Index for 'comment_id' may already exist or failed: {e}")

    async def search_similar_issues(self, query_text: str, limit: int = 5) -> list[models.ScoredPoint]:
        dense_vector = (await self.dense_vectors([query_text]))[0]
        sparse_vector = (await self.sparse_vectors([query_text]))[0]

        results = await self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=models.SparseVector(**sparse_vector.as_object()),
                    using="miniCOIL",
                    limit=10,
                ),
                models.Prefetch(
                    query=dense_vector,
                    using="dense",
                    score_threshold=0.9,
                    limit=10,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            search_params=models.SearchParams(
                quantization=models.QuantizationSearchParams(
                    ignore=False,
                    rescore=True,
                    oversampling=2.0,
                )
            ),
            limit=limit,
        )
        return results.points
