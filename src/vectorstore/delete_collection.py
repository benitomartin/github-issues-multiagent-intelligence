from src.vectorstore.qdrant_store import QdrantVectorStore


def main() -> None:
    vectorstore = QdrantVectorStore()
    vectorstore.delete_collection()


if __name__ == "__main__":
    main()
