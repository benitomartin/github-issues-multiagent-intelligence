import importlib
from typing import Any
from unittest.mock import patch

import pytest

from src.models.agent_models import ClassificationState, Recommendation


def get_graph() -> object:
    import src.agents.graph

    importlib.reload(src.agents.graph)
    return src.agents.graph.build_issue_workflow().compile()


async def run_graph(graph: object, state: dict) -> dict:
    if hasattr(graph, "ainvoke"):
        return await graph.ainvoke(state)
    elif callable(graph):
        return await graph(state)
    raise AttributeError("Graph has no 'ainvoke' or '__call__' method.")


@pytest.mark.asyncio
async def test_full_graph_blocks_on_output_guardrail_toxic() -> None:
    async def toxic_recommendation(state: Any) -> Any:
        state.recommendation = Recommendation(
            summary="You are an idiot and I hate you. This is terrible garbage and you should feel bad.", references=[]
        )
        return state

    def mock_input_guardrail(s: Any) -> Any:
        s.blocked = False
        return s

    def mock_issue_search(s: Any) -> Any:
        s.similar_issues = []
        return s

    def mock_classification(s: Any) -> Any:
        s.classification = ClassificationState(
            category="bug", priority="high", labels=["regression", "model"], assignee="johndoe"
        )
        return s

    with patch.multiple(
        "src.agents.agents",
        input_guardrail_agent=mock_input_guardrail,
        issue_search_agent=mock_issue_search,
        classification_agent=mock_classification,
        recommendation_agent=toxic_recommendation,
    ):
        result = await run_graph(get_graph(), {"title": "T", "body": "B"})
        assert result["blocked"]
        assert result["validation_summary"]["type"] == "ToxicLanguage_Output"


@pytest.mark.asyncio
async def test_full_graph_blocks_on_output_guardrail_secret() -> None:
    async def secret_recommendation(state: Any) -> Any:
        state.recommendation = Recommendation(summary="Here is the API_KEY: sk-123456789abcdef", references=[])
        return state

    def mock_input_guardrail(s: Any) -> Any:
        s.blocked = False
        return s

    def mock_issue_search(s: Any) -> Any:
        s.similar_issues = []
        return s

    def mock_classification(s: Any) -> Any:
        s.classification = ClassificationState(
            category="bug", priority="high", labels=["regression", "model"], assignee="johndoe"
        )
        return s

    with patch.multiple(
        "src.agents.agents",
        input_guardrail_agent=mock_input_guardrail,
        issue_search_agent=mock_issue_search,
        classification_agent=mock_classification,
        recommendation_agent=secret_recommendation,
    ):
        result = await run_graph(get_graph(), {"title": "T", "body": "B"})
        assert result["blocked"]
        assert result["validation_summary"]["type"] == "SecretsPresent_Output"


@pytest.mark.asyncio
async def test_full_graph_blocks_on_input_guardrail_secret() -> None:
    async def clean_recommendation(state: Any) -> Any:
        state.recommendation = Recommendation(summary="This is a clean and safe recommendation.", references=[])
        return state

    def mock_input_guardrail_secret(s: Any) -> Any:
        # Simulate secret detection blocking the input
        s.blocked = True
        s.validation_summary = {
            "type": "SecretsPresent_Input",
            "failure_reason": "Detected secret in input",
        }
        return s

    def mock_issue_search(s: Any) -> Any:
        s.similar_issues = []
        return s

    def mock_classification(s: Any) -> Any:
        s.classification = ClassificationState(
            category="bug", priority="high", labels=["regression", "model"], assignee="johndoe"
        )
        return s

    with patch.multiple(
        "src.agents.agents",
        input_guardrail_agent=mock_input_guardrail_secret,
        issue_search_agent=mock_issue_search,
        classification_agent=mock_classification,
        recommendation_agent=clean_recommendation,
    ):
        result = await run_graph(get_graph(), {"title": "API key leaked", "body": "Here is the API_KEY: sk-abc123"})
        assert result["blocked"]
        assert result["validation_summary"]["type"] == "SecretsPresent_Input"


@pytest.mark.asyncio
async def test_full_graph_allows_clean_output() -> None:
    async def clean_recommendation(state: Any) -> Any:
        state.recommendation = Recommendation(
            summary="This appears to be a question about HuberRegressor, a robust regression model in scikit-learn.",
            references=[],
        )
        return state

    def mock_input_guardrail(s: Any) -> Any:
        s.blocked = False
        return s

    def mock_issue_search(s: Any) -> Any:
        s.similar_issues = []
        return s

    def mock_classification(s: Any) -> Any:
        s.classification = ClassificationState(
            category="bug", priority="high", labels=["regression", "model"], assignee="johndoe"
        )
        return s

    with patch.multiple(
        "src.agents.agents",
        input_guardrail_agent=mock_input_guardrail,
        issue_search_agent=mock_issue_search,
        classification_agent=mock_classification,
        recommendation_agent=clean_recommendation,
    ):
        result = await run_graph(get_graph(), {"title": "T", "body": "B"})
        assert not result.get("blocked", False)
        assert "HuberRegressor" in result["recommendation"].summary
