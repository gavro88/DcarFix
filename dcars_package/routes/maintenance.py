# dcars_package/routes/maintenance.py
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone

router = APIRouter()

# חוקים לדוגמה
MAINTENANCE_RULES = {
    "engine_oil": {"km_interval": 15000, "time_interval_days": 365},
    "oil_filter": {"km_interval": 15000, "time_interval_days": 365},
    "air_filter": {"km_interval": 30000, "time_interval_days": 730},
    "brake_fluid": {"km_interval": 40000, "time_interval_days": 730},
    "coolant": {"km_interval": 60000, "time_interval_days": 1460},
}

class ServiceRecord:
    def __init__(self, vehicle_id: str, item: str, at_mileage: int, at_time: datetime):
        self.vehicle_id = vehicle_id
        self.item = item
        self.at_mileage = at_mileage
        self.at_time = at_time

def compute_due(vehicle_id: str, current_mileage: Optional[int], history: List[ServiceRecord], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    last_by_item: Dict[str, ServiceRecord] = {}
    for rec in history:
        if rec.vehicle_id != vehicle_id:
            continue
        cur = last_by_item.get(rec.item)
        if (cur is None) or (rec.at_time > cur.at_time) or (rec.at_mileage > cur.at_mileage):
            last_by_item[rec.item] = rec

    results = []
    for item, rule in MAINTENANCE_RULES.items():
        km_interval = rule["km_interval"]
        time_interval = timedelta(days=rule["time_interval_days"])
        last = last_by_item.get(item)

        if last:
            km_since = (current_mileage - last.at_mileage) if current_mileage is not None else None
            time_since = now - last.at_time
        else:
            km_since = current_mileage if current_mileage is not None else None
            time_since = timedelta.max

        due_by_km = (km_since is not None) and (km_since >= km_interval)
        due_by_time = time_since >= time_interval

        next_due_at_km = None
        if current_mileage is not None:
            base_km = last.at_mileage if last else 0
            next_due_at_km = base_km + km_interval

        km_ratio = (km_since / km_interval) if (km_since is not None and km_interval > 0) else 0.0
        time_ratio = (time_since / time_interval) if time_interval.total_seconds() > 0 else 0.0
        ratio = max(float(km_ratio), float(time_ratio))
        urgency_score = max(0, min(100, int(ratio * 100)))

        results.append({
            "item": item,
            "due": bool(due_by_km or due_by_time or last is None),
            "due_by_km": bool(due_by_km),
            "due_by_time": bool(due_by_time),
            "last_service_at_mileage": last.at_mileage if last else None,
            "last_service_at_time": last.at_time.isoformat() if last else None,
            "next_due_at_km": next_due_at_km,
            "urgency_score": urgency_score,
        })

    full = {
        "vehicle_id": vehicle_id,
        "current_mileage": current_mileage,
        "generated_at": now.isoformat(),
        "items": results,
    }
    due_only = [r for r in results if r["due"]]
    return {
        "full": full,
        "due": {
            "vehicle_id": vehicle_id,
            "current_mileage": current_mileage,
            "generated_at": now.isoformat(),
            "items": due_only,
        },
    }

@router.get("/full")
def maintenance_full(vehicle_id: str = Query(...), mileage: Optional[int] = Query(None)):
    history: List[ServiceRecord] = []  # TODO: לחבר ל-DB/records בעתיד
    res = compute_due(vehicle_id=vehicle_id, current_mileage=mileage, history=history)
    return res["full"]

@router.get("/due")
def maintenance_due(vehicle_id: str = Query(...), mileage: Optional[int] = Query(None)):
    history: List[ServiceRecord] = []  # TODO: לחבר ל-DB/records בעתיד
    res = compute_due(vehicle_id=vehicle_id, current_mileage=mileage, history=history)
    return res["due"]

@router.get("/records")
def maintenance_records(vehicle_id: str):
    # בסיסי עד שיהיה חיבור למסד
    return {"vehicle_id": vehicle_id, "records": []}