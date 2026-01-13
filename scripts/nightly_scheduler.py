#!/usr/bin/env python3
"""
Nightly scheduler for shuttle allocation system.

This script should run at 10 PM every night and performs:
1. Lock the current date (today) - no more modifications allowed
2. Run allocation for tomorrow
3. Auto-create daily requests for the day after tomorrow (based on user defaults)

Schedule this with cron:
0 22 * * * cd /path/to/pathable-backend && python3 scripts/nightly_scheduler.py
"""

import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.dailyLock import DailyLock
from app.db.allocationEngine import run_daily_allocation, auto_create_default_requests


def lock_date(db, target_date: date):
    """
    Lock a specific date to prevent further modifications.
    This is called at 10 PM for 'tomorrow', right before allocation runs.
    """
    existing_lock = db.query(DailyLock).filter(DailyLock.service_date == target_date).first()
    
    if existing_lock:
        if not existing_lock.is_locked:
            existing_lock.is_locked = True
            db.commit()
            print(f"✓ Locked date: {target_date}")
        else:
            print(f"ℹ Date already locked: {target_date}")
    else:
        new_lock = DailyLock(
            service_date=target_date,
            is_locked=True
        )
        db.add(new_lock)
        db.commit()
        print(f"✓ Created lock for date: {target_date}")


def main():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    print("\n" + "="*70)
    print("🕙 NIGHTLY SCHEDULER - 10 PM RUN")
    print("="*70)
    print(f"Today: {today}")
    print(f"Tomorrow: {tomorrow}")
    print(f"Day After: {day_after}")
    print("="*70 + "\n")
    
    db = SessionLocal()
    
    try:
        # ========================================
        # STEP 1: Lock tomorrow (deadline passed)
        # ========================================
        print("📌 STEP 1: Locking tomorrow's requests")
        lock_date(db, tomorrow)
        
        # ========================================
        # STEP 2: Run allocation for tomorrow
        # ========================================
        print("\n🚌 STEP 2: Running allocation for tomorrow")
        result = run_daily_allocation(db, tomorrow)
        print(f"✓ Allocation completed for {tomorrow}")
        print(f"  - Total requests: {result['total_requests']}")
        print(f"  - Groups allocated: {result['groups_allocated']}")
        print(f"  - High priority: {result['high_priority_allocated']}")
        print(f"  - Medium priority: {result['medium_priority_allocated']}")
        print(f"  - Low priority: {result['low_priority_allocated']}")
        print(f"  - Failed: {result['failed']}")
        
        # ========================================
        # STEP 3: Auto-create requests for day after tomorrow
        # ========================================
        print(f"\n📝 STEP 3: Auto-creating requests for {day_after}")
        created_count = auto_create_default_requests(db, day_after)
        print(f"✓ Created {created_count} default requests for {day_after}")
        
        print("\n" + "="*70)
        print("✅ NIGHTLY SCHEDULER COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
