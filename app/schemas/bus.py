from pydantic import BaseModel
from typing import List, Optional


class SeatResponse(BaseModel):
    seatId: str
    seatNumber: str
    isAvailable: bool
    allocatedUserId: Optional[str] = None
    allocatedUserName: Optional[str] = None


class BusResponse(BaseModel):
    busId: str
    routeName: str
    routeEndpoint: dict  # {lat, lng}
    capacity: int
    availableSeats: int
    seats: List[SeatResponse]


class AllocationStatsResponse(BaseModel):
    date: str
    totalRequests: int
    groupsAllocated: int
    highPriorityAllocated: int
    mediumPriorityAllocated: int
    lowPriorityAllocated: int
    failed: int


class UserBusAssignmentResponse(BaseModel):
    date: str
    status: str
    busId: Optional[str] = None
    routeName: Optional[str] = None
    seatNumber: Optional[str] = None
    pickupLocation: dict  # {lat, lng}
    message: str
