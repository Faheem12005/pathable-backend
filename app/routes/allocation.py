from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List

from app.db.database import SessionLocal
from app.db.allocationEngine import run_daily_allocation
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.route import Route
from app.models.booking import Booking
from app.models.user import User
from app.schemas.bus import (
    BusResponse,
    SeatResponse,
    AllocationStatsResponse,
    UserBusAssignmentResponse
)

router = APIRouter(prefix="/allocation", tags=["Allocation"])


def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/run", response_model=AllocationStatsResponse)
def runAllocation(targetDate: str = None, db: Session = Depends(getDb)):
    """
    Manually trigger the seat allocation process.
    
    - targetDate: Optional date in YYYY-MM-DD format (default: tomorrow)
    - This runs the priority-based allocation engine
    """
    try:
        if targetDate:
            target = datetime.strptime(targetDate, "%Y-%m-%d").date()
        else:
            target = date.today() + timedelta(days=1)
        
        stats = run_daily_allocation(db, target)
        
        return AllocationStatsResponse(
            date=stats["date"],
            totalRequests=stats["total_requests"],
            groupsAllocated=stats["groups_allocated"],
            highPriorityAllocated=stats["high_priority_allocated"],
            mediumPriorityAllocated=stats["medium_priority_allocated"],
            lowPriorityAllocated=stats["low_priority_allocated"],
            failed=stats["failed"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buses", response_model=List[BusResponse])
def getAllBuses(db: Session = Depends(getDb)):
    """
    Get all buses with their seat layouts and current allocations.
    Shows which seats are taken and by whom.
    """
    buses = db.query(Bus).all()
    
    response = []
    for bus in buses:
        route = db.query(Route).filter(Route.id == bus.route_id).first()
        seats = db.query(Seat).filter(Seat.bus_id == bus.id).order_by(Seat.seat_number).all()
        
        # Get today's bookings for this bus
        today_bookings = (
            db.query(Booking, User)
            .join(User, Booking.user_id == User.id)
            .filter(Booking.bus_id == bus.id, Booking.date == date.today())
            .all()
        )
        
        booking_map = {str(b.seat_id): u for b, u in today_bookings}
        
        seat_responses = []
        available_count = 0
        
        for seat in seats:
            user = booking_map.get(str(seat.id))
            if seat.is_available:
                available_count += 1
            
            seat_responses.append(SeatResponse(
                seatId=str(seat.id),
                seatNumber=seat.seat_number,
                isAvailable=seat.is_available,
                allocatedUserId=str(user.id) if user else None,
                allocatedUserName=user.name if user else None
            ))
        
        response.append(BusResponse(
            busId=str(bus.id),
            routeName=route.poi_name if route else "Unknown",
            routeEndpoint={"lat": route.end_lat, "lng": route.end_lng} if route else {"lat": 0, "lng": 0},
            capacity=bus.capacity,
            availableSeats=available_count,
            seats=seat_responses
        ))
    
    return response


@router.get("/bus/{busId}", response_model=BusResponse)
def getBusDetails(busId: str, db: Session = Depends(getDb)):
    """Get detailed seat layout for a specific bus"""
    bus = db.query(Bus).filter(Bus.id == busId).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    route = db.query(Route).filter(Route.id == bus.route_id).first()
    seats = db.query(Seat).filter(Seat.bus_id == busId).order_by(Seat.seat_number).all()
    
    # Get today's bookings
    today_bookings = (
        db.query(Booking, User)
        .join(User, Booking.user_id == User.id)
        .filter(Booking.bus_id == busId, Booking.date == date.today())
        .all()
    )
    
    booking_map = {str(b.seat_id): u for b, u in today_bookings}
    
    seat_responses = []
    available_count = 0
    
    for seat in seats:
        user = booking_map.get(str(seat.id))
        if seat.is_available:
            available_count += 1
        
        seat_responses.append(SeatResponse(
            seatId=str(seat.id),
            seatNumber=seat.seat_number,
            isAvailable=seat.is_available,
            allocatedUserId=str(user.id) if user else None,
            allocatedUserName=user.name if user else None
        ))
    
    return BusResponse(
        busId=str(bus.id),
        routeName=route.poi_name if route else "Unknown",
        routeEndpoint={"lat": route.end_lat, "lng": route.end_lng} if route else {"lat": 0, "lng": 0},
        capacity=bus.capacity,
        availableSeats=available_count,
        seats=seat_responses
    )


@router.get("/user/{userId}/assignment/{date}", response_model=UserBusAssignmentResponse)
def getUserAssignment(userId: str, date: str, db: Session = Depends(getDb)):
    """
    Get user's bus assignment for a specific date.
    Shows bus, route, seat number, and pickup location.
    """
    from app.models.dailyRequest import DailyRequest
    
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    
    request = db.query(DailyRequest).filter(
        DailyRequest.user_id == userId,
        DailyRequest.date == target_date
    ).first()
    
    if not request:
        return UserBusAssignmentResponse(
            date=date,
            status="NO_REQUEST",
            pickupLocation={"lat": 0, "lng": 0},
            message="No shuttle request for this date"
        )
    
    if request.status == "PENDING":
        return UserBusAssignmentResponse(
            date=date,
            status="PENDING",
            pickupLocation={"lat": request.request_lat, "lng": request.request_lng},
            message="Allocation pending. Check after 10 PM."
        )
    
    if request.status == "FAILED":
        return UserBusAssignmentResponse(
            date=date,
            status="FAILED",
            pickupLocation={"lat": request.request_lat, "lng": request.request_lng},
            message="Could not allocate seat. All buses full."
        )
    
    # Status is ALLOCATED
    bus = db.query(Bus).filter(Bus.id == request.allocated_bus_id).first()
    route = db.query(Route).filter(Route.id == bus.route_id).first() if bus else None
    seat = db.query(Seat).filter(Seat.id == request.allocated_seat_id).first()
    
    return UserBusAssignmentResponse(
        date=date,
        status="ALLOCATED",
        busId=str(bus.id) if bus else None,
        routeName=route.poi_name if route else "Unknown",
        seatNumber=seat.seat_number if seat else None,
        pickupLocation={"lat": request.request_lat, "lng": request.request_lng},
        message=f"Seat {seat.seat_number if seat else '?'} on {route.poi_name if route else 'bus'}"
    )
