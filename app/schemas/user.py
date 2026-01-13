from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum


class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class Location(BaseModel):
    lat: float
    lng: float


class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    homeLocation: Location
    daysRequired: List[DayOfWeek]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Faheem",
                "email": "faheem@vit.ac.in",
                "homeLocation": {"lat": 12.805748807464756, "lng": 80.22034842520952},
                "daysRequired": ["MON", "TUE", "WED"]
            }
        }


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    homeLocation: Location
    daysRequired: List[str]

    class Config:
        from_attributes = True


class DailyRequestCreate(BaseModel):
    """Request to modify shuttle for a specific date"""
    date: str  # Format: YYYY-MM-DD
    location: Optional[Location] = None  # If None, use default location

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-14",
                "location": {"lat": 12.81, "lng": 80.23}
            }
        }


class DailyRequestUpdate(BaseModel):
    """Update location for an existing daily request"""
    location: Location

    class Config:
        json_schema_extra = {
            "example": {
                "location": {"lat": 12.82, "lng": 80.24}
            }
        }


class DailyRequestResponse(BaseModel):
    id: str
    date: str
    location: Location
    isDefaultDay: bool
    isModified: bool
    status: str
    allocatedBusId: Optional[str] = None
    allocatedSeatId: Optional[str] = None


class AllocationStatusResponse(BaseModel):
    date: str
    status: str
    busId: Optional[str] = None
    seatId: Optional[str] = None
    seatNumber: Optional[str] = None
    message: str
