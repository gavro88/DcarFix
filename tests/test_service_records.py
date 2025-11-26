from fastapi.testclient import TestClient
from dcars_package.app import app

client = TestClient(app)

def test_crud_flow():
    r = client.post("/service-records", json={
        "vehicle_id": "v1",
        "item": "engine_oil",
        "at_mileage": 70000
    })
    assert r.status_code == 201
    rec = r.json()
    rid = rec["id"]

    r = client.get("/service-records", params={"vehicle_id": "v1"})
    assert r.status_code == 200
    assert any(x["id"] == rid for x in r.json())

    r = client.put(f"/service-records/{rid}", json={"at_mileage": 72000})
    assert r.status_code == 200
    assert r.json()["at_mileage"] == 72000

    r = client.delete(f"/service-records/{rid}")
    assert r.status_code == 204