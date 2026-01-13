from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime
from typing import List
import uuid

from app.db.database import SessionLocal
from app.models.user import User
from app.models.dailyRequest import DailyRequest
from app.schemas.user import (
    UserRegisterRequest, 
    UserResponse, 
    DailyRequestCreate,
    DailyRequestResponse,
    AllocationStatusResponse,
    Location
)
from app.db.lockUtils import isLocked

router = APIRouter(prefix="/user", tags=["User"])


def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def getDayAbbreviation(d: date) -> str:
    """Convert date to day abbreviation (MON, TUE, etc.)"""
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    return days[d.weekday()]


# ============================================
# USER REGISTRATION
# ============================================

@router.post("/register", response_model=UserResponse)
def registerUser(request: UserRegisterRequest, db: Session = Depends(getDb)):
    """
    Register a new user with default home location and required days.
    
    These become the user's DEFAULT preferences with HIGHEST priority
    for seat allocation.
    """
    try:
        user = User(
            id=uuid.uuid4(),
            name=request.name,
            email=request.email,
            home_lat=request.homeLocation.lat,
            home_lng=request.homeLocation.lng,
            default_days=[day.value for day in request.daysRequired]
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            homeLocation=Location(lat=user.home_lat, lng=user.home_lng),
            daysRequired=user.default_days
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{userId}", response_model=UserResponse)
def getUser(userId: str, db: Session = Depends(getDb)):
    """Get user details by ID"""
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        homeLocation=Location(lat=user.home_lat, lng=user.home_lng),
        daysRequired=user.default_days
    )


@router.get("/by-email/{email}", response_model=UserResponse)
def getUserByEmail(email: str, db: Session = Depends(getDb)):
    """Get user details by email (simple auth alternative)"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        homeLocation=Location(lat=user.home_lat, lng=user.home_lng),
        daysRequired=user.default_days
    )


# ============================================
# DAILY SHUTTLE REQUESTS
# ============================================

@router.post("/{userId}/request", response_model=DailyRequestResponse)
def createDailyRequest(
    userId: str, 
    request: DailyRequestCreate, 
    db: Session = Depends(getDb)
):
    """
    Create or update a shuttle request for a specific date.
    
    - If date is in user's default days AND location matches default → HIGH priority
    - If date is in user's default days BUT location changed → MEDIUM priority  
    - If date is NOT in user's default days → LOW priority (extra day request)
    
    Cannot create requests after 10 PM lock for that day.
    """
    # Check if locked
    requestDate = datetime.strptime(request.date, "%Y-%m-%d").date()
    
    if requestDate == date.today() and isLocked(db):
        raise HTTPException(
            status_code=400, 
            detail="Cannot modify requests after 10 PM deadline"
        )
    
    if requestDate < date.today():
        raise HTTPException(status_code=400, detail="Cannot create request for past date")

    # Get user
    user = db.query(User).filter(User.id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Determine if this is a default day
    dayAbbr = getDayAbbreviation(requestDate)
    isDefaultDay = dayAbbr in user.default_days

    # Determine location and if modified
    if request.location:
        reqLat = request.location.lat
        reqLng = request.location.lng
        # Check if location differs from default (with small tolerance)
        isModified = (
            abs(reqLat - user.home_lat) > 0.0001 or 
            abs(reqLng - user.home_lng) > 0.0001
        )
    else:
        # Use default location
        reqLat = user.home_lat
        reqLng = user.home_lng
        isModified = False

    # Check for existing request on this date
    existing = db.query(DailyRequest).filter(
        DailyRequest.user_id == userId,
        DailyRequest.date == requestDate
    ).first()

    if existing:
        # Update existing request
        existing.request_lat = reqLat
        existing.request_lng = reqLng
        existing.is_modified = True  # Any update marks as modified
        existing.status = "PENDING"
        db.commit()
        db.refresh(existing)
        dailyReq = existing
    else:
        # Create new request
        dailyReq = DailyRequest(
            id=uuid.uuid4(),
            user_id=userId,
            date=requestDate,
            request_lat=reqLat,
            request_lng=reqLng,
            is_default_day=isDefaultDay,
            is_modified=isModified,
            status="PENDING"
        )
        db.add(dailyReq)
        db.commit()
        db.refresh(dailyReq)

    return DailyRequestResponse(
        id=str(dailyReq.id),
        date=str(dailyReq.date),
        location=Location(lat=dailyReq.request_lat, lng=dailyReq.request_lng),
        isDefaultDay=dailyReq.is_default_day,
        isModified=dailyReq.is_modified,
        status=dailyReq.status,
        allocatedBusId=str(dailyReq.allocated_bus_id) if dailyReq.allocated_bus_id else None,
        allocatedSeatId=str(dailyReq.allocated_seat_id) if dailyReq.allocated_seat_id else None
    )


@router.delete("/{userId}/request/{date}")
def cancelDailyRequest(userId: str, date: str, db: Session = Depends(getDb)):
    """Cancel a shuttle request for a specific date (before 10 PM)"""
    requestDate = datetime.strptime(date, "%Y-%m-%d").date()
    
    if isLocked(db):
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel requests after 10 PM deadline"
        )

    existing = db.query(DailyRequest).filter(
        DailyRequest.user_id == userId,
        DailyRequest.date == requestDate
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Request not found")

    db.delete(existing)
    db.commit()
    
    return {"status": "cancelled", "date": date}


@router.get("/{userId}/requests", response_model=List[DailyRequestResponse])
def getUserRequests(userId: str, db: Session = Depends(getDb)):
    """Get all pending and upcoming requests for a user"""
    requests = db.query(DailyRequest).filter(
        DailyRequest.user_id == userId,
        DailyRequest.date >= date.today()
    ).order_by(DailyRequest.date).all()

    return [
        DailyRequestResponse(
            id=str(r.id),
            date=str(r.date),
            location=Location(lat=r.request_lat, lng=r.request_lng),
            isDefaultDay=r.is_default_day,
            isModified=r.is_modified,
            status=r.status,
            allocatedBusId=str(r.allocated_bus_id) if r.allocated_bus_id else None,
            allocatedSeatId=str(r.allocated_seat_id) if r.allocated_seat_id else None
        )
        for r in requests
    ]


@router.get("/{userId}/allocation/{date}", response_model=AllocationStatusResponse)
def getAllocationStatus(userId: str, date: str, db: Session = Depends(getDb)):
    """
    Get the allocation status for a specific date.
    Call this after 10 PM to see assigned bus and seat.
    """
    from app.models.seat import Seat
    
    requestDate = datetime.strptime(date, "%Y-%m-%d").date()
    
    request = db.query(DailyRequest).filter(
        DailyRequest.user_id == userId,
        DailyRequest.date == requestDate
    ).first()

    if not request:
        return AllocationStatusResponse(
            date=date,
            status="NO_REQUEST",
            message="No shuttle request found for this date"
        )

    if request.status == "PENDING":
        return AllocationStatusResponse(
            date=date,
            status="PENDING",
            message="Allocation pending. Check after 10 PM."
        )
    
    if request.status == "ALLOCATED":
        seat = db.query(Seat).filter(Seat.id == request.allocated_seat_id).first()
        return AllocationStatusResponse(
            date=date,
            status="ALLOCATED",
            busId=str(request.allocated_bus_id),
            seatId=str(request.allocated_seat_id),
            seatNumber=seat.seat_number if seat else None,
            message="Seat allocated successfully!"
        )
    
    return AllocationStatusResponse(
        date=date,
        status=request.status,
        message="Could not allocate seat. All buses full or no suitable route."
    )
