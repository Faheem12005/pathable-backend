import uuid
from sqlalchemy import Column, String, Date, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from datetime import datetime


class AllocationRun(Base):
    """
    Tracks each daily allocation run for audit and monitoring.
    One record per day, stores stats about the allocation process.
    """
    __tablename__ = "allocation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_date = Column(Date, nullable=False, unique=True)  # The date allocations are FOR
    executed_at = Column(DateTime, default=datetime.utcnow)  # When the allocation ran
    
    # Statistics
    total_requests = Column(Integer, default=0)
    groups_allocated = Column(Integer, default=0)
    high_priority_allocated = Column(Integer, default=0)
    medium_priority_allocated = Column(Integer, default=0)
    low_priority_allocated = Column(Integer, default=0)
    failed_allocations = Column(Integer, default=0)
    
    # Status: RUNNING, COMPLETED, FAILED
    status = Column(String, default="RUNNING")
    error_message = Column(String, nullable=True)
