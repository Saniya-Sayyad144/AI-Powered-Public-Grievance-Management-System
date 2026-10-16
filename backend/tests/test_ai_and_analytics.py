from fastapi.testclient import TestClient

from tests.conftest import bearer, create_account


def test_ai_recommendations_return_calculated_values(client: TestClient):
    create_account("citizen", "citizen@example.com")
    headers = bearer(client, "citizen@example.com")
    response = client.post("/api/ai/analyze", json={"title": "Contaminated water by the school", "description": "Brown water with a strong odor near children", "severity": 5, "safety_impact": True, "complaint_age_days": 4}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["category"]["category"] == "Water Supply"
    assert 0 <= data["category"]["confidence"] <= 1
    assert data["priority"]["priority"] == "Critical"
    assert data["review_required"] is True


def test_ai_requires_valid_input_and_dashboard_uses_database(client: TestClient):
    create_account("citizen", "citizen@example.com")
    headers = bearer(client, "citizen@example.com")
    invalid = client.post("/api/ai/analyze", json={"title": "x", "description": "tiny"}, headers=headers)
    assert invalid.status_code == 422
    dashboard = client.get("/api/dashboard/stats", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["data"]["total"] == 0
    categories = client.get("/api/ai/categories", headers=headers)
    assert categories.status_code == 200
    assert {item["name"] for item in categories.json()["data"]} == {"Roads", "Garbage", "Water Supply", "Drainage", "Streetlights"}
