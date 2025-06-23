from pydantic import BaseModel


# Input schema for the API
class IssueRequest(BaseModel):
    title: str
    body: str


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    graph_loaded: bool


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
    timestamp: float
