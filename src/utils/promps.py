class PromptTemplates:
    """Centralized class for all prompt templates used in the workflow."""

    @staticmethod
    def classification_prompt() -> str:
        return """
            You are a helpful assistant that classifies GitHub issues into categories, priorities,
            suggested labels, and recommends assignees.

            Issue Title: {title}
            Issue Body: {body}

            To give you more context, we have the following similar issues:

            {similar_issues}

            Classify the issue with the following structure:

            - category ((string)): one of: bug, feature, task, no type
            - priority ((string)): one of: high, medium, low
            - labels ((list of strings)): [
                "<relevant GitHub labels such as: bug, enhancement, good first issue, needs discussion, "
                "needs triage, API, performance, regression, classification, documentation, CI, tests>"
            ]
            - assignee ((string)): "<recommended team: @core-devs, @ml-team, @maintainers, or @frontend, "
            "@backend, @data-scientist>"

            Notes:
            - Use the issue body and title to infer what component or domain the issue touches
            (e.g., API, plotting, regression).
            - Use `bug` category if the report includes an error, unexpected behavior, or crash.
            - Use `enhancement` or `feature` if the issue requests new behavior or improvements.
            - Documentation issues should include appropriate doc-related labels.
            - When unsure of the assignee, suggest a relevant team (e.g., @ml-team for model-related issues).
            - Limit labels to 2–5 per issue, selecting only the most relevant.

            """

    @staticmethod
    def summary_prompt(state: dict, top_references: list[str]) -> str:
        return (
            f"The following GitHub issue has been classified as:\n"
            f"- Category: {state['classification']['category']}\n"
            f"- Priority: {state['classification']['priority']}\n"
            f"- Labels: {', '.join(state['classification']['labels'])}\n"
            f"- Assignee: {state['classification']['assignee']}\n\n"
            f"Here are the most similar past issues:\n"
            + "\n".join(f"- {url}" for url in top_references)
            + "\n\nWrite a helpful recommendation summary."
        )
