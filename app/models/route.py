import uuid
from sqlalchemy import Column, Float, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    end_lat = Column(Float, nullable=False)
    end_lng = Column(Float, nullable=False)
    poi_name = Column(String, nullable=False)
