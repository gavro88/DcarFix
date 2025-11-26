from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Query, Path as FPath, Response, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dcars_package.services.maintenance_logic import compute_due

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Dcars Maintenance API")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ===========================
# In-memory stores
# ===========================

MAINTENANCE_DB: Dict[str, Dict[str, Any]] = {}
SERVICE_RECORDS: List[Dict[str, Any]] = []  # {"id","vehicle_id","item","at_mileage","notes","created_at"}


# ===========================
# Basic endpoints
# ===========================

@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# ===========================
# Maintenance models & helpers
# ===========================

class UpsertBody(BaseModel):
    vehicle_id: str
    mileage: int
    avg_monthly_km: Optional[float] = None
    last_services: Optional[Dict[str, Dict[str, Any]]] = None  # {"item": {"last_km": int, "last_date": iso/datetime}}


def parse_last_services(payload: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Normalize last_services dict:
    - parse ISO date strings to datetime
    - keep last_km as-is
    """
    if not payload:
        return {}

    parsed: Dict[str, Dict[str, Any]] = {}
    for item, meta in payload.items():
        last_km = meta.get("last_km")
        last_date_raw = meta.get("last_date")
        last_date = None

        if isinstance(last_date_raw, str):
            try:
                last_date = datetime.fromisoformat(last_date_raw)
            except Exception:
                last_date = None
        elif isinstance(last_date_raw, datetime):
            last_date = last_date_raw

        parsed[item] = {"last_km": last_km, "last_date": last_date}

    return parsed


# ===========================
# Maintenance endpoints
# ===========================

@app.post("/vehicles/upsert")
def upsert_vehicle(body: UpsertBody):
    vehicle_id = body.vehicle_id

    if body.mileage < 0:
        raise HTTPException(status_code=400, detail="mileage must be >= 0")

    record = MAINTENANCE_DB.get(
        vehicle_id,
        {"last_services": {}, "avg_monthly_km": None, "mileage": 0},
    )

    record["mileage"] = body.mileage

    if body.avg_monthly_km is not None:
        record["avg_monthly_km"] = body.avg_monthly_km

    if body.last_services:
        record["last_services"].update(parse_last_services(body.last_services))

    MAINTENANCE_DB[vehicle_id] = record
    return {"ok": True, "vehicle_id": vehicle_id, "record": record}


@app.get("/vehicles")
def list_vehicles(vehicle_id: Optional[str] = Query(None)):
    if vehicle_id:
        rec = MAINTENANCE_DB.get(vehicle_id)
        return [dict(vehicle_id=vehicle_id, **rec)] if rec else []
    return [dict(vehicle_id=k, **v) for k, v in MAINTENANCE_DB.items()]


@app.get("/maintenance/due")
def maintenance_due(
    vehicle_id: str = Query(..., min_length=1),
    mileage: Optional[int] = Query(None),
):
    rec = MAINTENANCE_DB.get(vehicle_id)
    if not rec and mileage is None:
        return {"vehicle_id": vehicle_id, "any_due": False, "items": [], "overall_urgency": 0.0}

    current_km = mileage if mileage is not None else rec["mileage"]

    if current_km < 0:
        raise HTTPException(status_code=400, detail="mileage must be >= 0")

    last_services = rec["last_services"] if rec else {}
    avg_monthly_km = rec["avg_monthly_km"] if rec else None

    result = compute_due(
        vehicle_id=vehicle_id,
        current_km=current_km,
        last_services=last_services,
        avg_monthly_km=avg_monthly_km,
    )

    # expose only due / high-urgency items
    due_or_high = [it for it in result["items"] if it["due"] or it["urgency_score"] >= 0.75]

    return {
        "vehicle_id": vehicle_id,
        "any_due": result["any_due"],
        "items": due_or_high,
        "overall_urgency": result["overall_urgency"],
    }


@app.get("/maintenance/full")
def maintenance_full(
    vehicle_id: str = Query(..., min_length=1),
    mileage: Optional[int] = Query(None),
):
    rec = MAINTENANCE_DB.get(vehicle_id)
    current_km = mileage if mileage is not None else (rec["mileage"] if rec else 0)
    last_services = rec["last_services"] if rec else {}
    avg_monthly_km = rec["avg_monthly_km"] if rec else None

    return compute_due(
        vehicle_id=vehicle_id,
        current_km=current_km,
        last_services=last_services,
        avg_monthly_km=avg_monthly_km,
    )


# ===========================
# Service records endpoints
# ===========================

@app.post("/service-records", status_code=201)
def create_service_record(payload: Dict[str, Any]):
    vehicle_id = payload.get("vehicle_id")
    item = payload.get("item")
    at_mileage = payload.get("at_mileage")
    notes = payload.get("notes")

    if vehicle_id is None or item is None or at_mileage is None:
        raise HTTPException(status_code=422, detail="missing required fields: vehicle_id, item, at_mileage")

    try:
        at_mileage = int(at_mileage)
    except Exception:
        raise HTTPException(status_code=422, detail="at_mileage must be int")

    if at_mileage < 0:
        raise HTTPException(status_code=400, detail="at_mileage must be >= 0")

    rec = {
        "id": len(SERVICE_RECORDS) + 1,
        "vehicle_id": str(vehicle_id),
        "item": str(item),
        "at_mileage": at_mileage,
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    SERVICE_RECORDS.append(rec)

    MAINTENANCE_DB.setdefault(
        rec["vehicle_id"],
        {"last_services": {}, "avg_monthly_km": None, "mileage": at_mileage},
    )
    MAINTENANCE_DB[rec["vehicle_id"]]["mileage"] = max(
        MAINTENANCE_DB[rec["vehicle_id"]]["mileage"],
        at_mileage,
    )

    return rec


@app.get("/service-records")
def list_service_records(vehicle_id: Optional[str] = Query(None)):
    if vehicle_id:
        return [r for r in SERVICE_RECORDS if r["vehicle_id"] == vehicle_id]
    return SERVICE_RECORDS


@app.put("/service-records/{rid}", status_code=200)
async def update_service_record(
    request: Request,
    rid: int = FPath(..., ge=1),
):
    payload = await request.json()

    for rec in SERVICE_RECORDS:
        if rec["id"] == rid:
            # update mileage
            if "at_mileage" in payload:
                try:
                    new_m = int(payload["at_mileage"])
                except Exception:
                    raise HTTPException(status_code=422, detail="at_mileage must be int")

                if new_m < 0:
                    raise HTTPException(status_code=400, detail="at_mileage must be >= 0")

                rec["at_mileage"] = new_m
                vid = rec["vehicle_id"]

                MAINTENANCE_DB.setdefault(
                    vid,
                    {"last_services": {}, "avg_monthly_km": None, "mileage": new_m},
                )
                MAINTENANCE_DB[vid]["mileage"] = max(
                    MAINTENANCE_DB[vid]["mileage"],
                    new_m,
                )

            # update notes if present
            if "notes" in payload:
                rec["notes"] = payload["notes"]

            # return updated record (FastAPI -> status 200)
            return rec

    raise HTTPException(status_code=404, detail="record not found")


@app.delete("/service-records/{rid}", status_code=204)
def delete_service_record(rid: int = FPath(..., ge=1)):
    global SERVICE_RECORDS
    for i, rec in enumerate(SERVICE_RECORDS):
        if rec["id"] == rid:
            SERVICE_RECORDS.pop(i)
            return Response(status_code=204)
    
    raise HTTPException(status_code=404, detail="record not found")