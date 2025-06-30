import argparse
import asyncio

from langgraph.graph import END, StateGraph
from loguru import logger

from src.agents.agents import (
    classification_agent,
    input_guardrail_agent,
    issue_search_agent,
    output_guardrail_agent,
    recommendation_agent,
)
from src.models.agent_models import IssueState


def build_issue_workflow() -> StateGraph:
    builder = StateGraph(IssueState)
    builder.set_entry_point("Input Guardrail")

    builder.add_node("Input Guardrail", input_guardrail_agent)
    builder.add_node("Issue Search", issue_search_agent)
    builder.add_node("Classification", classification_agent)
    builder.add_node("Recommendation", recommendation_agent)
    builder.add_node("Output Guardrail", output_guardrail_agent)

    # Conditional branching
    def guardrail_condition(state: IssueState) -> str:
        return "pass" if not state.blocked else "block"

    builder.add_conditional_edges("Input Guardrail", guardrail_condition, {"pass": "Issue Search", "block": END})

    builder.add_edge("Issue Search", "Classification")
    builder.add_edge("Classification", "Recommendation")
    builder.add_edge("Recommendation", "Output Guardrail")

    # Branch for output guardrail
    builder.add_conditional_edges(
        "Output Guardrail",
        lambda s: "pass" if not s.blocked else "block",
        {"pass": END, "block": END},
    )
    return builder


# # For LangGraph Studio
# graph = build_issue_workflow().compile()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run research graph with custom parameters")
    parser.add_argument("--title", type=str, default="Huberregressor.", help="Issue Title")
    parser.add_argument(
        "--body",
        type=str,
        default="""
    def hello():
        user_id = "1234"
        user_pwd = "password1234"
        user_api_key = "sk-xhdfgtest"

    """,
        help="Issue Body",
    )
    args = parser.parse_args()

    async def main() -> dict:
        graph = build_issue_workflow().compile()
        result = await graph.ainvoke({"title": args.title, "body": args.body})

        if "recommendation" in result:
            logger.info("\n\n" + result["recommendation"].summary)

        if "validation_summary" in result:
            logger.info("\n\n" + "Title: " + args.title)
            logger.info("\n\n" + "Body: " + args.body)

            validation = result["validation_summary"]
            logger.info("\n\n" + "Validation Type: " + validation.get("type", "Unknown"))
            logger.info("\n\n" + "Failure Reason: " + validation.get("failure_reason", "Unknown"))

            if "score" in validation:
                logger.info("\n\n" + "Confidence Score: " + str(validation["score"]))

            if "error_spans" in validation:
                logger.info("\n\n" + "Error Spans:")
                for span in validation["error_spans"]:
                    logger.info(f"  - start: {span['start']}, end: {span['end']}, reason: {span['reason']}")

        return result

    try:
        result = asyncio.run(main())
    except Exception as e:
        logger.error(f"🔥 Unexpected workflow error: {e}")
