import pytest

from src.agents.agents import input_guardrail_agent
from src.models.agent_models import IssueState


@pytest.mark.asyncio
async def test_input_guardrail_blocks_toxic_input() -> None:
    # Create an actual IssueState object, not a dictionary
    state = IssueState(title="You're so dumb!", body="This code is trash, and so are you.")

    result = await input_guardrail_agent(state)
    assert result.blocked, "Toxic input should have been blocked"
    assert result.validation_summary is not None, "Validation summary should not be None"
    assert result.validation_summary["type"] == "ToxicLanguage_Input"


@pytest.mark.asyncio
async def test_input_guardrail_allows_clean_input() -> None:
    # Create an actual IssueState object, not a dictionary
    state = IssueState(
        title="Bug in HuberRegressor", body="I encountered unexpected behavior in the model when fitting certain data."
    )

    result = await input_guardrail_agent(state)
    assert not getattr(result, "blocked", False), "Clean input should not be blocked"
