from datetime import date
from app.db.database import SessionLocal
from app.models.dailyLock import DailyLock

db = SessionLocal()

today = date.today()
lock = db.query(DailyLock).filter(DailyLock.service_date == today).first()

if not lock:
    lock = DailyLock(service_date=today, is_locked=True)
    db.add(lock)
else:
    lock.is_locked = True

db.commit()
db.close()

print("Bookings locked for", today)
