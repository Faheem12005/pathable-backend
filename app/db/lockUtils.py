from datetime import date as date_type
from app.models.dailyLock import DailyLock


def ensureNotLocked(db):
    today = date_type.today()
    lock = db.query(DailyLock).filter(DailyLock.service_date == today).first()

    if lock and lock.is_locked:
        raise Exception("Bookings are locked for today")


def isLocked(db) -> bool:
    """Check if bookings are locked for today (after 10 PM processing)"""
    today = date_type.today()
    lock = db.query(DailyLock).filter(DailyLock.service_date == today).first()
    return lock and lock.is_locked


def isDateLocked(db, target_date: date_type) -> bool:
    """Check if bookings are locked for a specific date"""
    lock = db.query(DailyLock).filter(DailyLock.service_date == target_date).first()
    return lock and lock.is_locked
