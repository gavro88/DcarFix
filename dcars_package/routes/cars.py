from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.schemas import Car
from models.tables import CarTable
from db.session import get_db
from typing import List

router = APIRouter()

@router.get("/cars", response_model=List[Car])
def get_cars(db: Session = Depends(get_db)):
    return db.query(CarTable).all()
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models.schemas import Car, CarPart
from models.tables import CarTable, CarPartTable
from db.session import get_db

router = APIRouter()

# === כל הרכבים ===
@router.get("/cars", response_model=List[Car])
def get_cars(db: Session = Depends(get_db)):
    return db.query(CarTable).all()


# === חלקים לרכב מסוים ===
@router.get("/cars/{car_id}/parts", response_model=List[CarPart])
def get_car_parts(car_id: int, db: Session = Depends(get_db)):
    # נבדוק אם הרכב קיים
    car = db.query(CarTable).filter(CarTable.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="רכב לא נמצא")

    # נשלוף את כל ההתאמות שלו (CarPartTable)
    mappings = db.query(CarPartTable).filter(CarPartTable.car_id == car_id).all()
    if not mappings:
        return []

    return mappings