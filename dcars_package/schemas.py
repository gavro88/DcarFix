from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class ServiceRecordCreate(BaseModel):
    vehicle_id: str = Field(..., min_length=1)
    item: str = Field(..., min_length=1)
    at_mileage: int = Field(..., ge=0)
    at_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceRecordUpdate(BaseModel):
    item: Optional[str] = None
    at_mileage: Optional[int] = Field(None, ge=0)
    at_time: Optional[datetime] = None

class ServiceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    vehicle_id: str
    item: str
    at_mileage: int
    at_time: datetime