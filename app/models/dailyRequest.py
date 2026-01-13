import uuid
from sqlalchemy import Column, String, Float, Date, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class DailyRequest(Base):
    """
    Stores daily modifications to shuttle requests.
    
    When a user modifies their default schedule for a specific day,
    a record is created here. These users have LOWER priority than
    users using their defaults.
    
    Priority system:
    - is_default_day=True, is_modified=False → HIGHEST priority (using defaults)
    - is_default_day=True, is_modified=True → MEDIUM priority (modified their default)
    - is_default_day=False → LOWEST priority (added extra day not in defaults)
    """
    __tablename__ = "daily_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Location for this specific day (can differ from user's default)
    request_lat = Column(Float, nullable=False)
    request_lng = Column(Float, nullable=False)
    
    # Was this day in user's default schedule?
    is_default_day = Column(Boolean, default=False)
    
    # Did user modify their location for this day?
    is_modified = Column(Boolean, default=False)
    
    # Request status: PENDING, ALLOCATED, FAILED
    status = Column(String, default="PENDING")
    
    # Allocated bus and seat (filled after 10 PM processing)
    allocated_bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=True)
    allocated_seat_id = Column(UUID(as_uuid=True), ForeignKey("seats.id"), nullable=True)

    # Ensure one request per user per day
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='unique_user_date_request'),
    )
