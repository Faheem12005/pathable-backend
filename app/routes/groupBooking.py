from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.groupSeatBooking import bookGroupSeats

router = APIRouter(prefix="/group-booking")

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/auto")
def groupBook(groupId: str, busId: str, db: Session = Depends(getDb)):
    try:
        return bookGroupSeats(db, groupId, busId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
