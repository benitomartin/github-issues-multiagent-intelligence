import argparse
import asyncio

from langgraph.graph import END, StateGraph
from loguru import logger

from src.agents.agents import classification_agent, issue_search_agent, recommendation_agent
from src.models.agent_models import IssueState


def build_issue_workflow() -> StateGraph:
    builder = StateGraph(IssueState)
    builder.set_entry_point("Issue Search")

    builder.add_node("Issue Search", issue_search_agent)
    builder.add_node("Classification", classification_agent)
    builder.add_node("Recommendation", recommendation_agent)

    builder.add_edge("Issue Search", "Classification")
    builder.add_edge("Classification", "Recommendation")
    builder.add_edge("Recommendation", END)

    return builder


# For LangGraph Studio
graph = build_issue_workflow().compile()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run research graph with custom parameters")
    parser.add_argument("--title", type=str, default="Huber Loss for HistGradientBoostingRegressor", help="Issue Title")
    parser.add_argument("--body", type=str, default="Huber Loss for HistGradientBoostingRegressor", help="Issue Body")
    args = parser.parse_args()

    async def main() -> None:
        graph = build_issue_workflow().compile()
        result = await graph.ainvoke({"title": args.title, "body": args.body})
        logger.info("\n\n" + result["recommendation"]["summary"])

    asyncio.run(main())
