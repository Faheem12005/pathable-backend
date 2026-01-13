# Daily Request Lifecycle System

## Overview

The system automatically manages shuttle requests on a daily cycle with these phases:

1. **10 PM Night Before**: System auto-creates requests from user defaults
2. **Users Can Modify**: Until 10 PM the same day
3. **10 PM Deadline**: System locks date and runs allocation
4. **Results Available**: Users can view assigned bus and seat

## API Endpoints

### 1. Get User's Request for Specific Date
```
GET /user/{userId}/request/{date}
```

**Purpose**: Check if a request exists for a specific date (auto-created or manual)

**Response**:
```json
{
  "id": "uuid",
  "date": "2026-01-15",
  "location": {"lat": 12.805, "lng": 80.220},
  "isDefaultDay": true,
  "isModified": false,
  "status": "PENDING",
  "allocatedBusId": null,
  "allocatedSeatId": null
}
```

**Use Case**: Frontend calls this to see if user has a request for tomorrow, shows modify button if exists

### 2. Update Request Location
```
PUT /user/{userId}/request/{date}
Body: {
  "location": {"lat": 12.82, "lng": 80.24}
}
```

**Purpose**: Modify pickup location before 10 PM deadline

**Response**: Updated request with `isModified=true` (affects priority)

**Errors**:
- 400: Date is locked (deadline passed)
- 404: No request exists for this date
- 400: Request already allocated

**Priority Impact**:
- Unmodified default location = HIGH priority
- Modified location = MEDIUM priority

### 3. Get All User Requests
```
GET /user/{userId}/requests
```

Returns all pending and upcoming requests (today onwards)

### 4. Get Allocation Status
```
GET /user/{userId}/allocation/{date}
```

**Purpose**: Check if seat has been allocated (call after 10 PM)

**Response Statuses**:
- `NO_REQUEST`: No shuttle request for this date
- `PENDING`: Allocation not yet run (before 10 PM)
- `ALLOCATED`: Seat assigned
- `FAILED`: Could not allocate (buses full)

### 5. Cancel Request (DEPRECATED - Use PUT with different date instead)
```
DELETE /user/{userId}/request/{date}
```

## System Flow

### Timeline for January 15th Request:

**January 14, 10:00 PM**
- System calls `auto_create_default_requests(2026-01-15)`
- Creates DailyRequest for all users with "THU" in `default_days`
- Uses user's home location (`home_lat`, `home_lng`)
- Sets `is_default_day=True`, `is_modified=False` → HIGH priority

**January 15, 9:00 AM - 10:00 PM**
- User can view: `GET /user/{userId}/request/2026-01-15`
- User can modify: `PUT /user/{userId}/request/2026-01-15`
- Each modification sets `is_modified=True` → MEDIUM priority

**January 15, 10:00 PM**
1. System creates DailyLock for 2026-01-15 (`is_locked=True`)
2. Runs allocation: `run_daily_allocation(db, 2026-01-15)`
3. Processes groups (adjacent seats)
4. Allocates individuals by priority:
   - HIGH: Default location, unmodified
   - MEDIUM: Default location, modified
   - LOW: Extra day (not in defaults)
5. Updates `allocated_bus_id` and `allocated_seat_id`
6. Creates allocation_runs record with statistics

**January 16, onwards**
- User views result: `GET /user/{userId}/allocation/2026-01-15`
- Shows bus name, seat number, pickup location

## Data Models

### DailyRequest
```python
{
  "id": UUID,
  "user_id": UUID,
  "date": Date,
  "request_lat": Float,
  "request_lng": Float,
  "is_default_day": Boolean,  # Was this in user's default schedule?
  "is_modified": Boolean,      # Did user change location from default?
  "status": String,            # PENDING, ALLOCATED, FAILED
  "allocated_bus_id": UUID,
  "allocated_seat_id": UUID
}
```

### AllocationRun
```python
{
  "id": UUID,
  "run_date": Date (unique),  # Which day was allocated
  "executed_at": DateTime,     # When allocation ran
  "status": String,            # RUNNING, COMPLETED, FAILED
  "total_requests": Int,
  "groups_allocated": Int,
  "high_priority_allocated": Int,
  "medium_priority_allocated": Int,
  "low_priority_allocated": Int,
  "failed_allocations": Int,
  "error_message": String
}
```

### DailyLock
```python
{
  "service_date": Date (primary key),
  "is_locked": Boolean
}
```

## Priority System

**HIGH Priority** (First allocated)
- User has day in `default_days`
- Request auto-created by system
- Location NOT modified (using home location)
- `is_default_day=True, is_modified=False`

**MEDIUM Priority** (Second allocated)
- User has day in `default_days`
- Location modified via PUT endpoint
- `is_default_day=True, is_modified=True`

**LOW Priority** (Last allocated)
- User manually added extra day not in defaults
- `is_default_day=False`

## Nightly Scheduler

Schedule with cron: `0 22 * * * /path/to/nightly_scheduler.py`

The script:
1. Locks tomorrow (no more modifications)
2. Runs allocation for tomorrow
3. Auto-creates requests for day after tomorrow

```bash
# Manual test
python3 scripts/nightly_scheduler.py
```

## Frontend Integration

### Show Tomorrow's Request
```typescript
// On app open, fetch tomorrow's request
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const dateStr = tomorrow.toISOString().split('T')[0];

const response = await fetch(`/user/${userId}/request/${dateStr}`);
if (response.ok) {
  const request = await response.json();
  // Show "Your request for tomorrow" card
  // Show "Modify Location" button
} else if (response.status === 404) {
  // No request for tomorrow
  // Either: not a default day, or system hasn't created yet
}
```

### Modify Location
```typescript
async function modifyLocation(userId, date, newLat, newLng) {
  const response = await fetch(`/user/${userId}/request/${date}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      location: {lat: newLat, lng: newLng}
    })
  });
  
  if (response.ok) {
    const updated = await response.json();
    alert(`Location updated! ${updated.isModified ? '(Medium priority)' : ''}`);
  } else if (response.status === 400) {
    alert('Deadline passed! Cannot modify after 10 PM the day before.');
  }
}
```

### Check Allocation (After 10 PM)
```typescript
const response = await fetch(`/user/${userId}/allocation/${dateStr}`);
const allocation = await response.json();

switch (allocation.status) {
  case 'PENDING':
    // Show "Allocation will run at 10 PM"
    break;
  case 'ALLOCATED':
    // Show bus name, seat number, map
    console.log(`Seat: ${allocation.seatNumber}`);
    console.log(`Bus: ${allocation.routeName}`);
    break;
  case 'FAILED':
    // Show "No seats available, try different location"
    break;
  case 'NO_REQUEST':
    // Show "No request for this date"
    break;
}
```

## Testing

### Test Auto-Creation
```bash
python3 scripts/test_auto_create.py
```

### Test Manual Update
```bash
# Create a request for tomorrow (system would do this at 10 PM)
curl -X PUT "http://localhost:8000/user/USER_ID/request/2026-01-16" \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 12.82, "lng": 80.24}}'

# Verify modification
curl "http://localhost:8000/user/USER_ID/request/2026-01-16"
```

### Test Allocation
```bash
# Run allocation for specific date
curl -X POST "http://localhost:8000/allocation/run?date=2026-01-16"

# Check allocation status
curl "http://localhost:8000/user/USER_ID/allocation/2026-01-16"
```

## Error Handling

### Common Errors

1. **404 on GET /user/{userId}/request/{date}**
   - Request doesn't exist yet
   - Either not a default day, or system hasn't created yet (before 10 PM previous night)

2. **400 on PUT - "Deadline passed"**
   - Trying to modify after 10 PM
   - Date is locked in `daily_lock` table

3. **400 on PUT - "Already allocated"**
   - Request status is ALLOCATED
   - Cannot modify past requests

4. **FAILED status in allocation**
   - All buses full
   - No matching route for location
   - Group size exceeds available adjacent seats

## Database Queries

### Check what requests will be created tomorrow night
```sql
SELECT email, default_days 
FROM users 
WHERE default_days @> ARRAY['WED']::varchar[];
```

### See all requests for a date
```sql
SELECT u.email, dr.date, dr.is_default_day, dr.is_modified, dr.status
FROM daily_requests dr
JOIN users u ON u.id = dr.user_id
WHERE dr.date = '2026-01-15'
ORDER BY dr.is_default_day DESC, dr.is_modified ASC;
```

### Check allocation history
```sql
SELECT run_date, status, total_requests, 
       high_priority_allocated, medium_priority_allocated, 
       low_priority_allocated, failed_allocations
FROM allocation_runs
ORDER BY run_date DESC;
```

### See locks
```sql
SELECT service_date, is_locked
FROM daily_lock
ORDER BY service_date DESC;
```
