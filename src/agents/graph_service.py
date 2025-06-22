# src/agents/services.py

from langchain_openai import ChatOpenAI

from src.models.agent_models import ResponseFormatter
from src.utils.config import settings
from src.vectorstore.qdrant_store import AsyncQdrantVectorStore


class AgentServices:
    def __init__(self) -> None:
        from pydantic import SecretStr

        self.qdrant_store = AsyncQdrantVectorStore()
        self.llm = ChatOpenAI(
            temperature=settings.TEMPERATURE, model=settings.LLM_MODEL_NAME, api_key=SecretStr(settings.OPENAI_API_KEY)
        )
        self.llm_with_tools = self.llm.bind_tools([ResponseFormatter])


services = AgentServices()
