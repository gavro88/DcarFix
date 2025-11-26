# dcars_package/routes/service_records.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from dcars_package.schemas import ServiceRecordCreate, ServiceRecordUpdate, ServiceRecordResponse

router = APIRouter()

# In-memory repo (זמני עד DB)
class InMemoryServiceRecords:
    def __init__(self):
        self._data: List[ServiceRecordResponse] = []

    def list(self, vehicle_id: Optional[str] = None) -> List[ServiceRecordResponse]:
        if vehicle_id:
            return [r for r in self._data if r.vehicle_id == vehicle_id]
        return list(self._data)

    def get(self, record_id: str) -> Optional[ServiceRecordResponse]:
        return next((r for r in self._data if r.id == record_id), None)

    def create(self, payload: ServiceRecordCreate) -> ServiceRecordResponse:
        rec = ServiceRecordResponse(
            id=str(uuid.uuid4()),
            vehicle_id=payload.vehicle_id,
            item=payload.item,
            at_mileage=payload.at_mileage,
            at_time=payload.at_time or datetime.now(timezone.utc),
        )
        self._data.append(rec)
        return rec

    def update(self, record_id: str, payload: ServiceRecordUpdate) -> Optional[ServiceRecordResponse]:
        rec = self.get(record_id)
        if not rec:
            return None
        new = ServiceRecordResponse(
            id=rec.id,
            vehicle_id=rec.vehicle_id,
            item=payload.item if payload.item is not None else rec.item,
            at_mileage=payload.at_mileage if payload.at_mileage is not None else rec.at_mileage,
            at_time=payload.at_time if payload.at_time is not None else rec.at_time,
        )
        self._data = [r if r.id != record_id else new for r in self._data]
        return new

    def delete(self, record_id: str) -> bool:
        prev = len(self._data)
        self._data = [r for r in self._data if r.id != record_id]
        return len(self._data) < prev

repo = InMemoryServiceRecords()

@router.get("", response_model=List[ServiceRecordResponse])
def list_records(vehicle_id: Optional[str] = Query(None)):
    return repo.list(vehicle_id)

@router.post("", response_model=ServiceRecordResponse, status_code=201)
def create_record(payload: ServiceRecordCreate):
    return repo.create(payload)

@router.put("/{record_id}", response_model=ServiceRecordResponse)
def update_record(record_id: str, payload: ServiceRecordUpdate):
    out = repo.update(record_id, payload)
    if not out:
        raise HTTPException(status_code=404, detail="Record not found")
    return out

@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: str):
    ok = repo.delete(record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Record not found")
    return