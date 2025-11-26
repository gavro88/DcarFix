# tests/test_api.py
from fastapi.testclient import TestClient
from dcars_package.app import app

client = TestClient(app)

def test_root():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_swagger():
    r = client.get("/docs")
    assert r.status_code in (200, 404)

def test_all_parts():
    r = client.get("/maintenance/full", params={"vehicle_id": "v1", "mileage": 80000})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data

def test_maintenance():
    r = client.get("/maintenance/due", params={"vehicle_id": "v1", "mileage": 80000})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data

def test_maintenance_due_only():
    r = client.get("/maintenance/due", params={"vehicle_id": "v1"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data