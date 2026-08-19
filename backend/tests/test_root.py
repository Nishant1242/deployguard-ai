from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_returns_expected_response() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "DeployGuard AI API is running",
    }
