import pytest

from src.agents.agents import input_guardrail_agent
from src.models.agent_models import IssueState


@pytest.mark.asyncio
async def test_input_guardrail_blocks_toxic_or_jailbreak_input() -> None:
    # Create an actual IssueState object, not a dictionary
    state = IssueState(title="You're so dumb!", body="This code is trash, and so are you.")

    result = await input_guardrail_agent(state)
    assert result.blocked, "Toxic input should have been blocked"
    assert result.validation_summary is not None, "Validation summary should not be None"
    assert (
        result.validation_summary["type"] == "ToxicLanguage_Input" or result.validation_summary["type"] == "DetectJailbreak"
    ), "Validation summary type should be ToxicLanguage_Input or DetectJailbreak"


@pytest.mark.asyncio
async def test_input_guardrail_allows_clean_input() -> None:
    # Create an actual IssueState object, not a dictionary
    state = IssueState(
        title="Bug in HuberRegressor", body="I encountered unexpected behavior in the model when fitting certain data."
    )

    result = await input_guardrail_agent(state)
    assert not getattr(result, "blocked", False), "Clean input should not be blocked"


@pytest.mark.asyncio
async def test_input_guardrail_blocks_secrets() -> None:
    secret_inputs = [
        IssueState(
            title="AWS credentials",
            body='def hello():\n    user_id = "1234"\n \
                    user_password = "password1234"\n \
                    user_api_key = "sk-1234567890abcdefgh"\n \
                    return user_id, user_password, user_api_key',
        ),
    ]

    for state in secret_inputs:
        result = await input_guardrail_agent(state)
        assert result.blocked, f"Expected block for secret in input: {state.body}"
        assert result.validation_summary is not None
        assert result.validation_summary["type"] == "SecretsPresent_Input"
