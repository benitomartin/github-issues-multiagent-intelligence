import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.agents.graph import build_issue_workflow
from src.models.agent_models import IssueState
from src.models.api_model import ErrorResponse, HealthResponse, IssueRequest

# Global cache
compiled_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events"""
    global compiled_graph
    logger.info("🚀 Starting up Issue Processing API...")

    # Pre-compile the graph for better performance
    try:
        compiled_graph = build_issue_workflow().compile()
        logger.info("✅ Workflow graph compiled successfully")
    except Exception as e:
        logger.error(f"❌ Failed to compile workflow graph: {e}")
        raise

    yield

    logger.info("🛑 Shutting down Issue Processing API...")


app = FastAPI(
    title="GitHub Issue Processing API",
    description="Process GitHub issues, classify them, and provide recommendations.",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Internal server error", error_type=type(exc).__name__, timestamp=time.time()
        ).model_dump(),
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Response:
    start_time = time.time()

    # Log incoming request
    logger.info(f"📨 {request.method} {request.url}")

    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")

    return response


# Dependency for graph access
async def get_compiled_graph() -> Any:
    """Dependency to get the compiled workflow graph"""
    if compiled_graph is None:
        logger.error("Workflow graph not initialized")
        raise HTTPException(status_code=503, detail="Workflow graph not initialized. Service starting up.")
    return compiled_graph


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health() -> HealthResponse:
    """Health check endpoint with detailed status"""
    return HealthResponse(
        status="healthy" if compiled_graph is not None else "initializing",
        timestamp=time.time(),
        graph_loaded=compiled_graph is not None,
    )


# Readiness check (different from health - indicates ready to serve)
@app.get("/ready", tags=["Health"])
def readiness() -> dict[str, Any]:
    """Readiness check for Kubernetes/container orchestration"""
    if compiled_graph is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready", "timestamp": time.time(), "components": {"workflow_graph": "loaded"}}


# Main processing endpoint
@app.post("/process-issue", response_model=IssueState, tags=["Processing"])
async def process_issue(
    request: IssueRequest,
    graph: Annotated[Any, Depends(get_compiled_graph)],
) -> IssueState:
    """
    Process an issue for secret detection and analysis.

    This endpoint analyzes the provided issue title and body for:
    - Secret detection (API keys, passwords, tokens)
    - Security recommendations
    - Issue classification

    Returns detailed analysis results including any detected secrets
    and security recommendations.
    """
    start_time = time.time()

    try:
        # Log processing start
        logger.info(f"🔍 Processing issue: '{request.title}' (body length: {len(request.body)} chars)")

        # Process the issue
        result = await graph.ainvoke(
            {
                "title": request.title,
                "body": request.body,
            }
        )

        # Log processing completion
        processing_time = time.time() - start_time

        # Create response
        response = IssueState(**result)

        # Log results summary
        blocked_status = "🚫 BLOCKED" if response.blocked else "✅ PASSED"
        logger.info(f"🏁 Issue processed: '{request.title}' - {blocked_status} - Time: {processing_time:.3f}s")

        # Log validation details if blocked
        if response.blocked and hasattr(response, "validation_summary"):
            validation = response.validation_summary
            if isinstance(validation, dict):
                failure_reason = validation.get("failure_reason", "Unknown")
                logger.warning(f"🔴 Blocking reason: {failure_reason}")

        return response

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"💥 Processing failed for '{request.title}': {str(e)} (after {processing_time:.3f}s)")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}") from e


# Validation endpoint
@app.post("/validate", tags=["Processing"])
async def validate_issue(request: IssueRequest, graph: Annotated[Any, Depends(get_compiled_graph)]) -> dict[str, Any]:
    """
    Quick validation check for an issue (lighter than full processing).
    Returns basic validation results without detailed recommendations.
    """
    try:
        result = await graph.ainvoke(
            {
                "title": request.title,
                "body": request.body,
            }
        )

        response = IssueState(**result)

        return {
            "valid": not response.blocked,
            "blocked": response.blocked,
            "validation_summary": getattr(response, "validation_summary", None),
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}") from e


# Stats endpoint
@app.get("/stats", tags=["Monitoring"])
def get_stats() -> dict[str, Any]:
    """Get basic API statistics"""
    return {
        "service": "Issue Processing API",
        "version": "1.0.0",
        "uptime_seconds": time.time(),
        "graph_status": "loaded" if compiled_graph else "not_loaded",
        "endpoints": [
            "/health - Health check",
            "/ready - Readiness check",
            "/process-issue - Main processing",
            "/validate - Quick validation",
            "/stats - This endpoint",
        ],
    }


# PRODUCTION CORS (commented out - uncomment for production)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://my-issue-helper.streamlit.app",
#         "https://your-frontend-domain.com"
#     ],
#     allow_credentials=True,
#     allow_methods=["GET", "POST"],
#     allow_headers=["Content-Type", "Authorization"],
# )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
