from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from dcars_package.db import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String, primary_key=True, index=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)

    maintenance_items = relationship("MaintenanceItem", back_populates="vehicle")
    service_records = relationship("ServiceRecord", back_populates="vehicle")


class MaintenanceItem(Base):
    __tablename__ = "maintenance_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), index=True)
    code = Column(String, index=True)
    name = Column(String)
    interval_km = Column(Integer)
    price = Column(Float)

    vehicle = relationship("Vehicle", back_populates="maintenance_items")


class ServiceRecord(Base):
    __tablename__ = "service_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), index=True)
    date = Column(Date)
    mileage = Column(Integer)
    total_cost = Column(Float, default=0.0)

    vehicle = relationship("Vehicle", back_populates="service_records")
    items = relationship("ServiceRecordItem", back_populates="record", cascade="all, delete")


class ServiceRecordItem(Base):
    __tablename__ = "service_record_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("service_records.id", ondelete="CASCADE"), index=True)
    code = Column(String, index=True)

    record = relationship("ServiceRecord", back_populates="items")