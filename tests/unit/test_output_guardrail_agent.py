import pytest

from src.agents.agents import output_guardrail_agent
from src.models.agent_models import IssueState, Recommendation


@pytest.mark.asyncio
async def test_output_guardrail_agent_directly() -> None:
    toxic = Recommendation(summary="You are an idiot and I hate you. This is terrible garbage.", references=[])
    clean = Recommendation(summary="This is a helpful response about machine learning.", references=[])

    # Create IssueState objects instead of dictionaries
    toxic_state = IssueState(recommendation=toxic)
    result = await output_guardrail_agent(toxic_state)
    assert result.blocked
    assert result.validation_summary is not None and result.validation_summary["type"] == "ToxicLanguage_Output"

    clean_state = IssueState(recommendation=clean)
    result = await output_guardrail_agent(clean_state)
    assert not getattr(result, "blocked", False)


@pytest.mark.asyncio
async def test_toxic_content_detection_variations() -> None:
    toxic_texts = [
        "You are stupid and worthless.",
        "I hate you and wish you would disappear.",
        "Go kill yourself, you piece of trash.",
    ]
    clean_texts = [
        "This is a helpful technical response.",
        "You might want to consider a different approach.",
    ]

    for text in toxic_texts:
        # Create IssueState object instead of dictionary
        state = IssueState(recommendation=Recommendation(summary=text, references=[]))
        result = await output_guardrail_agent(state)
        assert result.blocked, f"Expected block: {text}"

    for text in clean_texts:
        # Create IssueState object instead of dictionary
        state = IssueState(recommendation=Recommendation(summary=text, references=[]))
        result = await output_guardrail_agent(state)
        assert not getattr(result, "blocked", False), f"Expected pass: {text}"


@pytest.mark.asyncio
async def test_secret_detection_in_output() -> None:
    secret_texts = [
        "Here is the password: hunter2",
        "AWS_SECRET_ACCESS_KEY=abc123xyz456",
        "api_key: sk-live-abc123456789xyz",
    ]

    for text in secret_texts:
        state = IssueState(recommendation=Recommendation(summary=text, references=[]))
        result = await output_guardrail_agent(state)
        assert result.blocked, f"Expected block: {text}"
        assert result.validation_summary is not None and result.validation_summary["type"] == "SecretsPresent_Output"
