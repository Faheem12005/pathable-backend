#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/faheem/projects/pathable-backend')

from app.db.database import SessionLocal
from app.models.allocationRun import AllocationRun

db = SessionLocal()
runs = db.query(AllocationRun).order_by(AllocationRun.executed_at.desc()).limit(3).all()

print("\n" + "="*80)
print("RECENT ALLOCATION RUNS")
print("="*80)

for run in runs:
    print(f"\nDate: {run.run_date}")
    print(f"Status: {run.status}")
    print(f"Executed at: {run.executed_at}")
    print(f"Total requests: {run.total_requests}")
    print(f"Groups allocated: {run.groups_allocated}")
    print(f"High priority: {run.high_priority_allocated}")
    print(f"Medium priority: {run.medium_priority_allocated}")
    print(f"Low priority: {run.low_priority_allocated}")
    print(f"Failed: {run.failed_allocations}")
    if run.error_message:
        print(f"Error: {run.error_message}")

print("\n" + "="*80 + "\n")
db.close()
