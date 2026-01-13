import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.seat import Seat
from app.models.booking import Booking
from app.models.groupMember import GroupMember
from app.db.lockUtils import ensureNotLocked


def bookGroupSeats(db: Session, groupId: str, busId: str):
    """
    Books ADJACENT seats for ALL members of a group in ONE transaction.

    Guarantees:
    - 10 PM daily lock enforced FIRST
    - All-or-nothing booking
    - Adjacent seat allocation
    - Row-level locking
    """

    # 🔒 1️⃣ HARD STOP — enforce 10 PM lock FIRST
    ensureNotLocked(db)

    try:
        # 👥 2️⃣ Fetch group members
        members = (
            db.query(GroupMember)
            .filter(GroupMember.group_id == groupId)
            .all()
        )

        if not members:
            raise Exception("Group has no members")

        group_size = len(members)

        # 🔐 3️⃣ Lock ALL available seats on the bus
        seats = (
            db.execute(
                select(Seat)
                .where(Seat.bus_id == busId)
                .where(Seat.is_available == True)
                .order_by(Seat.seat_number)
                .with_for_update()
            )
            .scalars()
            .all()
        )

        if len(seats) < group_size:
            raise Exception("No adjacent seats available")

        # 🔎 4️⃣ Find adjacent seat block
        for i in range(len(seats) - group_size + 1):
            block = seats[i:i + group_size]

            seat_numbers = [s.seat_number for s in block]

            if _areSeatsAdjacent(seat_numbers):
                # 📝 5️⃣ Book seats atomically
                for seat, member in zip(block, members):
                    seat.is_available = False

                    booking = Booking(
                        id=uuid.uuid4(),
                        user_id=member.user_id,
                        bus_id=busId,
                        seat_id=seat.id,
                        date=date.today(),
                        status="CONFIRMED"
                    )
                    db.add(booking)

                db.commit()
                return {
                    "status": "GROUP_BOOKED",
                    "groupSize": group_size
                }

        # ❌ 6️⃣ No adjacent block found
        raise Exception("No adjacent seats available")

    except Exception as e:
        db.rollback()
        raise e


def _areSeatsAdjacent(seat_numbers):
    """
    Example:
    ['A1', 'A2', 'A3'] → True
    ['A1', 'A3'] → False
    """
    try:
        nums = [int(s[1:]) for s in seat_numbers]
        return nums == list(range(nums[0], nums[0] + len(nums)))
    except Exception:
        return False
