from datetime import date
from app.models.dailyLock import DailyLock


def ensureNotLocked(db):
    today = date.today()
    lock = db.query(DailyLock).filter(DailyLock.service_date == today).first()

    if lock and lock.is_locked:
        raise Exception("Bookings are locked for today")


def isLocked(db) -> bool:
    """Check if bookings are locked for today (after 10 PM processing)"""
    today = date.today()
    lock = db.query(DailyLock).filter(DailyLock.service_date == today).first()
    return lock and lock.is_locked
