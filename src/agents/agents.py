from langchain_core.messages import AIMessage

from src.agents.graph_service import services
from src.models.agent_models import ClassificationState, IssueState, Recommendation
from src.utils.promps import PromptTemplates

# ========================================
# Vector Search Agent
# ========================================


async def issue_search_agent(state: IssueState) -> IssueState:
    try:
        query_text = f"{state.get('title', '')} {state.get('body', '')}"
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

        state["similar_issues"] = similar_issues
        return state

    except Exception as e:
        state.setdefault("errors", []).append(f"Async vector search error: {str(e)}")
        return state


# ========================================
# Classification Agent
# ========================================


async def classification_agent(state: IssueState) -> IssueState:
    try:
        prompt = PromptTemplates.classification_prompt().format(
            title=state["title"], body=state["body"], similar_issues=state["similar_issues"]
        )

        response: AIMessage = await services.llm_with_tools.ainvoke(prompt)  # type: ignore
        parsed = response.tool_calls[0]["args"]  # Parsed dict output

        state["classification"] = ClassificationState(**dict(parsed))  # type: ignore
        return state

    except Exception as e:
        state.setdefault("errors", []).append(f"Classification error: {str(e)}")
        return state


async def recommendation_agent(state: IssueState) -> IssueState:
    try:
        # Get top similar issue URLs
        top_references = []
        seen_urls = set()

        for issue in state.get("similar_issues", []):
            url = issue["url"]
            if url not in seen_urls:
                top_references.append(url)
                seen_urls.add(url)
            if len(top_references) == 4:
                break

        prompt = PromptTemplates.summary_prompt(dict(state), top_references)

        response = await services.llm.ainvoke(prompt)

        if isinstance(response.content, str):
            summary = response.content.strip()
        elif isinstance(response.content, list):
            # Join list items as string, or handle as needed
            summary = " ".join(str(item) for item in response.content).strip()
        else:
            summary = str(response.content).strip()

        state["recommendation"] = Recommendation(summary=summary, references=top_references)

        # logger.info(f"Recommendation summary: {summary}")

        return state

    except Exception as e:
        state.setdefault("errors", []).append(f"Recommendation error: {str(e)}")
        return state
