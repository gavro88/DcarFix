from sqlalchemy.orm import Session
from dcars_package import models


def seed(db: Session):
    # אם כבר קיים רכב – לא נזרע שוב
    if db.query(models.Vehicle).first():
        print("⚠️ Data already exists, skipping seed.")
        return

    vehicles = [
        models.Vehicle(id="ABC123", make="Toyota", model="Corolla", year=2018),
        models.Vehicle(id="XYZ987", make="Mazda", model="3", year=2017),
        models.Vehicle(id="LMN456", make="Honda", model="Civic", year=2019),
    ]
    db.add_all(vehicles)

    items = [
        # Toyota Corolla
        models.MaintenanceItem(vehicle_id="ABC123", code="OIL_FILTER",
                               name="פילטר שמן", interval_km=15000, price=80),
        models.MaintenanceItem(vehicle_id="ABC123", code="ENGINE_OIL",
                               name="שמן מנוע", interval_km=15000, price=200),
        models.MaintenanceItem(vehicle_id="ABC123", code="AIR_FILTER",
                               name="פילטר אוויר", interval_km=20000, price=100),

        # Mazda 3
        models.MaintenanceItem(vehicle_id="XYZ987", code="OIL_FILTER",
                               name="פילטר שמן", interval_km=15000, price=90),
        models.MaintenanceItem(vehicle_id="XYZ987", code="ENGINE_OIL",
                               name="שמן מנוע", interval_km=15000, price=210),
        models.MaintenanceItem(vehicle_id="XYZ987", code="CABIN_FILTER",
                               name="פילטר תא נוסעים", interval_km=20000, price=120),

        # Honda Civic
        models.MaintenanceItem(vehicle_id="LMN456", code="OIL_FILTER",
                               name="פילטר שמן", interval_km=15000, price=85),
        models.MaintenanceItem(vehicle_id="LMN456", code="ENGINE_OIL",
                               name="שמן מנוע", interval_km=15000, price=205),
        models.MaintenanceItem(vehicle_id="LMN456", code="AIR_FILTER",
                               name="פילטר אוויר", interval_km=25000, price=110),
    ]
    db.add_all(items)
    db.commit()
    print("✅ Seed completed: Vehicles & Maintenance items inserted")