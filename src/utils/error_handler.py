# src/utils/error_utils.py


from src.models.agent_models import IssueState


class ErrorHandler:
    @staticmethod
    def log_error(state: IssueState, error: Exception, context: str | None = None) -> IssueState:
        if not hasattr(state, "errors") or state.errors is None:
            state.errors = []

        prefix = f"{context} error: " if context else "Error: "
        state.errors.append(prefix + str(error))
        state.blocked = True

        return state
