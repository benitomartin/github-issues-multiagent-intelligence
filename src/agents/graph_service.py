# # src/agents/services.py

from langchain_openai import ChatOpenAI
from loguru import logger

from src.models.agent_models import ResponseFormatter
from src.utils.config import settings
from src.vectorstore.qdrant_store import AsyncQdrantVectorStore


class AgentServices:
    def __init__(self) -> None:
        # Initialize vector store
        self.qdrant_store = AsyncQdrantVectorStore()

        # Try initializing the OpenAI Chat model
        try:
            self.llm = ChatOpenAI(
                temperature=settings.TEMPERATURE, model=settings.LLM_MODEL_NAME, api_key=settings.OPENAI_API_KEY
            )
            self.llm_with_tools = self.llm.bind_tools([ResponseFormatter])
            logger.info("ChatOpenAI initialized successfully.")

        except ValueError as e:
            # Handle cases where the API key or other parameters are missing or invalid
            logger.error(f"Failed to initialize ChatOpenAI due to invalid values: {e}")
            raise

        except Exception as e:
            # Catch any other exceptions, e.g., network issues, invalid API key, etc.
            logger.error(f"An error occurred while initializing ChatOpenAI: {e}")
            raise


# Instantiate the AgentServices
services = AgentServices()
