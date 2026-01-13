import uuid
from sqlalchemy import Column, Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class Seat(Base):
    __tablename__ = "seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    seat_number = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)
