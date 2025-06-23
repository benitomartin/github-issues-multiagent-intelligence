import pytest
from httpx import ASGITransport, AsyncClient

import src.api.main as main_module
from src.agents.graph import build_issue_workflow
from src.api.main import app
from src.models.api_model import IssueRequest


@pytest.mark.asyncio
async def test_get_health_ready_and_process_issue() -> None:
    # Clear the graph
    main_module.compiled_graph = None

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        health_resp = await ac.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "initializing"

        ready_resp = await ac.get("/ready")
        assert ready_resp.status_code == 503

    # Build and compile the real graph
    graph = build_issue_workflow().compile()

    # Patch the global variable inside the app's module
    main_module.compiled_graph = graph

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        health_resp = await ac.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        ready_resp = await ac.get("/ready")
        assert ready_resp.status_code == 200

        # Normal issue: expect blocked == False
        issue_request = IssueRequest(title="Test issue", body="Some body text")
        process_resp = await ac.post("/process-issue", json=issue_request.model_dump())
        assert process_resp.status_code == 200
        data = process_resp.json()
        assert data["title"] == "Test issue"
        assert data["blocked"] is False

        # Toxic issue: expect blocked == True
        toxic_request = IssueRequest(title="Toxic comment", body="you are an idiot")
        process_resp_toxic = await ac.post("/process-issue", json=toxic_request.model_dump())
        assert process_resp_toxic.status_code == 200
        toxic_data = process_resp_toxic.json()
        assert toxic_data["title"] == "Toxic comment"
        assert toxic_data["blocked"] is True

        # Secret issue: expect blocked == True
        toxic_request = IssueRequest(
            title="Secret in comment",
            body='def hello():\n    user_id = "1234"\n \
                    user_password = "password1234"\n \
                    user_api_key = "sk-1234567890abcdefgh"\n \
                    return user_id, user_password, user_api_key',
        )
        process_resp_toxic = await ac.post("/process-issue", json=toxic_request.model_dump())
        assert process_resp_toxic.status_code == 200
        toxic_data = process_resp_toxic.json()
        assert toxic_data["title"] == "Secret in comment"
        assert toxic_data["blocked"] is True
