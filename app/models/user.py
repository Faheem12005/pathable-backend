import uuid
from sqlalchemy import Column, String, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    
    # Default home location (lat/lng)
    home_lat = Column(Float, nullable=False)
    home_lng = Column(Float, nullable=False)
    
    # Default days user needs shuttle (e.g., ["MON", "TUE", "WED"])
    default_days = Column(ARRAY(String), nullable=False, default=[])

