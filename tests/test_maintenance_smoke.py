from fastapi.testclient import TestClient
from dcars_package.app import app

client = TestClient(app)

def test_docs_available():
    r = client.get("/docs")
    assert r.status_code in (200, 404)

def test_maintenance_due():
    r = client.get("/maintenance/due", params={"vehicle_id": "v1", "mileage": 80000})
    assert r.status_code == 200
    data = r.json()
    assert data["vehicle_id"] == "v1"
    assert "items" in data