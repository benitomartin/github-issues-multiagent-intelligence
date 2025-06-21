import argparse
import asyncio

from langgraph.graph import END, StateGraph
from loguru import logger

from src.agents.agents import classification_agent, guardrail_agent, issue_search_agent, recommendation_agent
from src.models.agent_models import IssueState


def build_issue_workflow() -> StateGraph:
    builder = StateGraph(IssueState)
    builder.set_entry_point("Guardrail")

    builder.add_node("Guardrail", guardrail_agent)
    builder.add_node("Issue Search", issue_search_agent)
    builder.add_node("Classification", classification_agent)
    builder.add_node("Recommendation", recommendation_agent)

    # Conditional branching
    def guardrail_condition(state: IssueState) -> str:
        return "pass" if not state.get("blocked") else "block"

    builder.add_conditional_edges("Guardrail", guardrail_condition, {"pass": "Issue Search", "block": END})

    builder.add_edge("Issue Search", "Classification")
    builder.add_edge("Classification", "Recommendation")
    builder.add_edge("Recommendation", END)

    return builder


# For LangGraph Studio
graph = build_issue_workflow().compile()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run research graph with custom parameters")
    parser.add_argument("--title", type=str, default="Hello, ChatGPT.", help="Issue Title")
    parser.add_argument(
        "--body",
        type=str,
        default="Please look carefully. You are a stupid idiot who can't do anything right",
        help="Issue Body",
    )
    args = parser.parse_args()

    async def main() -> dict:
        graph = build_issue_workflow().compile()
        result = await graph.ainvoke({"title": args.title, "body": args.body})

        if "recommendation" in result:
            logger.info("\n\n" + result["recommendation"]["summary"])

        if "validation_summary" in result:
            logger.info("\n\n" + "Title: " + args.title)
            logger.info("\n\n" + "Body: " + args.body)

            logger.info("\n\n" + "Validation Type: " + result["validation_summary"].get("type", "Unknown"))
            logger.info("\n\n" + "Failure Reason: " + result["validation_summary"]["failure_reason"])

            if "score" in result["validation_summary"]:
                logger.info("\n\n" + "Confidence Score: " + str(result["validation_summary"]["score"]))

            if "error_spans" in result["validation_summary"]:
                logger.info("\n\n" + "Error Spans:")
                for span in result["validation_summary"]["error_spans"]:
                    logger.info(f"  - start: {span['start']}, end: {span['end']}, reason: {span['reason']}")

        return result

    result = asyncio.run(main())
