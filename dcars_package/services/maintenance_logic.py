from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

DEFAULT_RULES = {
    "engine_oil": {"km_interval": 15000, "months_interval": 12, "caprice": 0.1},
    "oil_filter": {"km_interval": 15000, "months_interval": 12, "caprice": 0.08},
    "air_filter": {"km_interval": 30000, "months_interval": 24, "caprice": 0.05},
    "cabin_filter": {"km_interval": 20000, "months_interval": 18, "caprice": 0.05},
    "brake_fluid": {"km_interval": 60000, "months_interval": 24, "caprice": 0.12},
    "coolant": {"km_interval": 80000, "months_interval": 48, "caprice": 0.1},
    "spark_plugs": {"km_interval": 60000, "months_interval": 48, "caprice": 0.07},
}

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def compute_item_due(
    *,
    item: str,
    current_km: int,
    last_service_km: Optional[int],
    last_service_date: Optional[datetime],
    avg_monthly_km: Optional[float],
    rules: Dict[str, Any] = DEFAULT_RULES,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    rule = rules.get(item)
    if not rule:
        return {"item": item, "due": False, "reason": "no_rule", "urgency_score": 0.0}

    km_interval = rule["km_interval"]
    months_interval = rule["months_interval"]
    caprice = rule.get("caprice", 0.0)

    km_since = None if last_service_km is None else max(0, current_km - last_service_km)
    days_since = None if last_service_date is None else (now - last_service_date).days

    due_km_at = (last_service_km or 0) + km_interval
    due_time_at = (last_service_date or now) + timedelta(days=months_interval * 30)

    if km_since is None:
        km_ratio, km_remaining = 0.5, None
    else:
        km_ratio = clamp(km_since / km_interval)
        km_remaining = (due_km_at - current_km)

    if days_since is None:
        time_ratio, days_remaining = 0.5, None
    else:
        time_ratio = clamp(days_since / (months_interval * 30))
        days_remaining = (due_time_at - now).days

    w_km, w_time = 0.6, 0.4
    base_score = w_km * km_ratio + w_time * time_ratio
    urgency_score = clamp(base_score + 0.5 * caprice)

    due_flag = (km_ratio >= 1.0) or (time_ratio >= 1.0)

    next_due_at = {
        "km": max(due_km_at, current_km) if km_remaining is not None else due_km_at,
        "date": due_time_at.isoformat(),
    }

    return {
        "item": item,
        "due": bool(due_flag),
        "km_remaining": km_remaining,
        "days_remaining": days_remaining,
        "next_due_at": next_due_at,
        "urgency_score": urgency_score,
        "details": {
            "km_ratio": km_ratio,
            "time_ratio": time_ratio,
            "caprice": caprice,
            "rules": rule,
        },
    }

def compute_due(
    *,
    vehicle_id: str,
    current_km: int,
    last_services: Dict[str, Dict[str, Any]],
    avg_monthly_km: Optional[float] = None,
    rules: Dict[str, Any] = DEFAULT_RULES,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    results = []
    for item in rules.keys():
        meta = last_services.get(item, {})
        res = compute_item_due(
            item=item,
            current_km=current_km,
            last_service_km=meta.get("last_km"),
            last_service_date=meta.get("last_date"),
            avg_monthly_km=avg_monthly_km,
            rules=rules,
            now=now,
        )
        results.append(res)
    overall_urgency = max((r["urgency_score"] for r in results), default=0.0)
    any_due = any(r["due"] for r in results)
    return {
        "vehicle_id": vehicle_id,
        "current_km": current_km,
        "any_due": any_due,
        "overall_urgency": overall_urgency,
        "items": results,
        "generated_at": now.isoformat(),
    }
