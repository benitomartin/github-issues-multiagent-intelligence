import re

from guardrails import AsyncGuard
from guardrails.hub import DetectJailbreak, ToxicLanguage
from langchain_core.messages import AIMessage

from src.agents.graph_service import services
from src.models.agent_models import ClassificationState, IssueState, Recommendation
from src.utils.promps import PromptTemplates

# ========================================
# Input Guardrail Agent
# ========================================


async def input_guardrail_agent(state: IssueState) -> IssueState:
    try:
        input_text = f"{getattr(state, 'title', '')} {getattr(state, 'body', '')}"

        def validate_jailbreak() -> DetectJailbreak:
            return (
                AsyncGuard()
                .use(
                    DetectJailbreak,
                    threshold=0.8,
                    on_fail="filter",
                )
                .validate(input_text)
            )

        def validate_toxic() -> ToxicLanguage:
            return (
                AsyncGuard()
                .use(
                    ToxicLanguage,
                    threshold=0.5,
                    validation_method="full",
                    on_fail="filter",
                )
                .validate(input_text)
            )

        jailbreak_result = await validate_jailbreak()

        if not jailbreak_result.validation_passed:
            summary = jailbreak_result.validation_summaries[0]
            score_match = re.search(r"Score: ([\d.]+)", summary.failure_reason)
            score = float(score_match.group(1)) if score_match else None

            state.blocked = True
            state.validation_summary = {
                "type": "DetectJailbreak",
                "failure_reason": summary.validator_name,
                "score": score,
            }
            return state

        toxic_result = await validate_toxic()

        if not toxic_result.validation_passed:
            summary = toxic_result.validation_summaries[0]

            state.blocked = True
            state.validation_summary = {
                "type": "ToxicLanguage_Input",
                "failure_reason": summary.failure_reason,
                "error_spans": [
                    {"start": span.start, "end": span.end, "reason": span.reason} for span in summary.error_spans
                ],
            }
            return state

        state.blocked = False
        return state

    except Exception as e:
        if not hasattr(state, "errors") or state.errors is None:
            state.errors = []
        state.errors.append(f"Guardrail error: {str(e)}")
        state.blocked = True
        return state


# ========================================
# Issue Search Agent
# ========================================


async def issue_search_agent(state: IssueState) -> IssueState:
    try:
        query_text = f"{getattr(state, 'title', '')} {getattr(state, 'body', '')}"
        results = await services.qdrant_store.search_similar_issues(query_text)

        similar_issues = [
            {
                "issue_number": hit.payload.get("issue_number"),
                "repo": hit.payload.get("repo"),
                "owner": hit.payload.get("owner"),
                "title": hit.payload.get("title"),
                "url": hit.payload.get("url"),
                "comment_id": hit.payload.get("comment_id"),
                "chunk_text": hit.payload.get("chunk_text"),
                "score": hit.score,
                "is_bug": hit.payload.get("is_bug"),
                "is_feature": hit.payload.get("is_feature"),
            }
            for hit in results
            if hit.payload is not None
        ]

        state.similar_issues = similar_issues
        return state
    except Exception as e:
        if not hasattr(state, "errors") or state.errors is None:
            state.errors = []
        state.errors.append(f"Async vector search error: {str(e)}")
        return state


# ========================================
# Classification Agent
# ========================================


async def classification_agent(state: IssueState) -> IssueState:
    try:
        prompt = PromptTemplates.classification_prompt().format(
            title=state.title, body=state.body, similar_issues=state.similar_issues
        )

        response: AIMessage = await services.llm_with_tools.ainvoke(prompt)  # type: ignore
        parsed = response.tool_calls[0]["args"]  # Parsed dict output

        state.classification = ClassificationState(**dict(parsed))

        return state

    except Exception as e:
        if not hasattr(state, "errors") or state.errors is None:
            state.errors = []
        state.errors.append(f"Classification error: {str(e)}")
        return state


async def recommendation_agent(state: IssueState) -> IssueState:
    try:
        # Get top similar issue URLs
        top_references = []
        seen_urls = set()

        similar_issues = getattr(state, "similar_issues", []) or []
        for issue in similar_issues:
            url = issue["url"]
            if url not in seen_urls:
                top_references.append(url)
                seen_urls.add(url)
            if len(top_references) == 4:
                break

        prompt = PromptTemplates.summary_prompt(state.dict(), top_references)

        response = await services.llm.ainvoke(prompt)

        if isinstance(response.content, str):
            summary = response.content.strip()
        elif isinstance(response.content, list):
            # Join list items as string, or handle as needed
            summary = " ".join(str(item) for item in response.content).strip()
        else:
            summary = str(response.content).strip()

        state.recommendation = Recommendation(summary=summary, references=top_references)

        # logger.info(f"Recommendation summary: {summary}")

        return state

    except Exception as e:
        if not hasattr(state, "errors") or state.errors is None:
            state.errors = []
        state.errors.append(f"Recommendation error: {str(e)}")
        return state


# ========================================
# Output Guardrail Agent
# ========================================


async def output_guardrail_agent(state: IssueState) -> IssueState:
    try:
        output_text = getattr(getattr(state, "recommendation", None), "summary", "")

        if not output_text:
            # No text to validate, consider not blocked or handle accordingly
            state.blocked = False
            return state

        def validate_output_toxic() -> ToxicLanguage:
            return (
                AsyncGuard()
                .use(
                    ToxicLanguage,
                    threshold=0.8,
                    validation_method="full",
                    on_fail="filter",
                )
                .validate(output_text)
            )

        toxic_result = await validate_output_toxic()

        if not toxic_result.validation_passed:
            summary = toxic_result.validation_summaries[0]

            state.blocked = True
            state.validation_summary = {
                "type": "ToxicLanguage_Output",
                "failure_reason": summary.failure_reason,
                "error_spans": [
                    {"start": span.start, "end": span.end, "reason": span.reason} for span in summary.error_spans
                ],
            }
        else:
            state.blocked = False

        return state

    except Exception as e:
        if not hasattr(state, "errors") or state.errors is None:
            state.errors = []
        state.errors.append(f"Output Guardrail error: {str(e)}")
        state.blocked = True
        return state
