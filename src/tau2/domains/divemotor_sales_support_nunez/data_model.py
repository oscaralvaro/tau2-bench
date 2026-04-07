from tau2.environment.db import DB
from pydantic import BaseModel
from typing import Dict


class User(BaseModel):
    user_id: str
    name: str
    income: float


class Vehicle(BaseModel):
    vehicle_id: str
    brand: str
    model: str
    price: float


class Lead(BaseModel):
    user_id: str
    interest: str


class TestDrive(BaseModel):
    user_id: str
    vehicle_id: str
    date: str


class DivemotorDB(DB):
    users: Dict[str, User]
    vehicles: Dict[str, Vehicle]
    leads: Dict[str, Lead]
    test_drives: Dict[str, TestDrive]