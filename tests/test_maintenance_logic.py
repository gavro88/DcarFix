# tests/test_maintenance_logic.py
from datetime import datetime
from fastapi.testclient import TestClient
from dcars_package.app import app
from dcars_package.services.maintenance_logic import compute_due

client = TestClient(app)

def test_compute_due_by_km():
    now = datetime(2025, 1, 1)
    last_date = datetime(2024, 1, 1)
    res = compute_due(
        vehicle_id="V1",
        current_km=16000,
        last_services={"engine_oil": {"last_km": 0, "last_date": last_date}},
        now=now
    )
    oil = next(i for i in res["items"] if i["item"] == "engine_oil")
    assert oil["due"] is True
    assert oil["km_remaining"] is not None and oil["km_remaining"] <= 0

def test_compute_due_by_time():
    now = datetime(2025, 1, 1)
    last_date = datetime(2023, 6, 1)  # ~19 חודשים
    res = compute_due(
        vehicle_id="V2",
        current_km=5000,
        last_services={"cabin_filter": {"last_km": 0, "last_date": last_date}},
        now=now
    )
    item = next(i for i in res["items"] if i["item"] == "cabin_filter")
    assert item["due"] is True  # עבר חלון הזמן של 18 חודשים

def test_router_validation_and_filtering():
    # מיילג' שלילי נכשל
    bad = client.post("/vehicles/upsert", json={"vehicle_id": "V3", "mileage": -10})
    assert bad.status_code == 400

    # הכנסת שתי מכוניות, סינון לפי vehicle_id
    ok1 = client.post("/vehicles/upsert", json={"vehicle_id": "A1", "mileage": 10000})
    ok2 = client.post("/vehicles/upsert", json={"vehicle_id": "B2", "mileage": 20000})
    assert ok1.status_code == 200 and ok2.status_code == 200

    all_ = client.get("/vehicles")
    assert all_.status_code == 200
    data_all = all_.json()
    ids = {rec["vehicle_id"] for rec in data_all}
    assert "A1" in ids and "B2" in ids

    only_b2 = client.get("/vehicles", params={"vehicle_id": "B2"})
    assert only_b2.status_code == 200
    data_b2 = only_b2.json()
    assert len(data_b2) == 1 and data_b2[0]["vehicle_id"] == "B2"