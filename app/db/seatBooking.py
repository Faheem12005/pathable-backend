import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.seat import Seat
from app.models.booking import Booking
from app.db.lockUtils import ensureNotLocked


def bookSeat(db: Session, userId: str, busId: str):
    """
    Books ONE seat for a user on a bus.
    Enforces:
    - 10 PM daily lock
    - Row-level locking
    - No double booking
    """

    # 🔒 1️⃣ HARD STOP — enforce 10 PM lock FIRST
    ensureNotLocked(db)

    try:
        # 🔐 2️⃣ Find ONE available seat and lock it
        seat = (
            db.execute(
                select(Seat)
                .where(Seat.bus_id == busId)
                .where(Seat.is_available == True)
                .limit(1)
                .with_for_update()
            )
            .scalars()
            .first()
        )

        if not seat:
            raise Exception("No seats available")

        # 🚫 3️⃣ Mark seat unavailable
        seat.is_available = False

        # 📝 4️⃣ Create booking record
        booking = Booking(
            id=uuid.uuid4(),
            user_id=userId,
            bus_id=busId,
            seat_id=seat.id,
            date=date.today(),
            status="CONFIRMED"
        )

        db.add(booking)
        db.commit()

        return {
            "bookingId": str(booking.id),
            "seatId": str(seat.id),
            "status": "CONFIRMED"
        }

    except Exception as e:
        db.rollback()
        raise e
