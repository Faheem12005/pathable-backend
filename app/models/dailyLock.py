from sqlalchemy import Column, Date, Boolean
from app.db.database import Base

class DailyLock(Base):
    __tablename__ = "daily_lock"

    service_date = Column(Date, primary_key=True)
    is_locked = Column(Boolean, default=False)
