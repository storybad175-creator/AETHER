import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_regions_endpoint():
    response = client.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()

def test_invalid_uid():
    response = client.get("/player?uid=123&region=IND")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID"
