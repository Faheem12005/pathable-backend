#!/usr/bin/env python3
"""
Test the nightly scheduler with a future date
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.allocationEngine import auto_create_default_requests

# Test auto-creation for day after tomorrow
db = SessionLocal()
test_date = date.today() + timedelta(days=2)

print(f"\n🧪 Testing auto-creation for: {test_date}")
print(f"   Day of week: {test_date.strftime('%A')}\n")

created = auto_create_default_requests(db, test_date)
print(f"\n✅ Created {created} requests for {test_date}\n")

db.close()
