import time

from fastembed import SparseTextEmbedding, TextEmbedding
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, models

from src.utils.config import settings


class QdrantVectorStore:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

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

    def dense_vectors(self, texts: list[str]) -> list:
        return list(self.dense_model.embed(texts))

    def sparse_vectors(self, texts: list[str]) -> list:
        return list(self.sparse_model.embed(texts))

    def create_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            print(f"Collection '{self.collection_name}' already exists.")
            return

        start = time.time()
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": models.VectorParams(size=self.embedding_size, distance=Distance.COSINE)},
            quantization_config=self.quantization_config,
            sparse_vectors_config=self.sparse_vectors_config,
        )
        logger.info(f"Collection '{self.collection_name}' created in {time.time() - start:.2f}s.")

    def delete_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' deleted.")

    def create_indexes(self) -> None:
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="issue_number",
                field_schema=PayloadSchemaType.INTEGER,
            )
        except Exception as e:
            logger.info(f"Index for 'issue_number' may already exist or failed: {e}")

        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="comment_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
        except Exception as e:
            logger.info(f"Index for 'comment_id' may already exist or failed: {e}")
