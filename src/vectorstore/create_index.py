from src.vectorstore.qdrant_store import QdrantVectorStore


def main() -> None:
    vectorstore = QdrantVectorStore()
    vectorstore.create_indexes()


if __name__ == "__main__":
    main()
