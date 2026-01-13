from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.seatBooking import bookSeat

router = APIRouter()

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/booking/auto")
def autoBookSeat(userId: str, busId: str, db: Session = Depends(getDb)):
    try:
        booking = bookSeat(db, userId, busId)
        return {
            "bookingId": str(booking.id),
            "seatId": str(booking.seat_id),
            "status": booking.status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
