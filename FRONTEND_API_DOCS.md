# Frontend API Documentation - Daily Request Management

## Base URL
```
http://localhost:8000
```

For Android device with ADB reverse:
```
http://localhost:8000
```

---

## 1. Get Specific Daily Request

**Purpose**: Fetch a user's shuttle request for a specific date to display in UI or check if request exists before showing modify button.

### Endpoint
```
GET /user/{userId}/request/{date}
```

### Path Parameters
| Parameter | Type   | Description                           |
|-----------|--------|---------------------------------------|
| userId    | string | User UUID                             |
| date      | string | Date in YYYY-MM-DD format (e.g., 2026-01-15) |

### Request Headers
```
Content-Type: application/json
```

### Request Body
None

### Success Response (200 OK)
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "date": "2026-01-15",
  "location": {
    "lat": 12.805748807464756,
    "lng": 80.22034842520952
  },
  "isDefaultDay": true,
  "isModified": false,
  "status": "PENDING",
  "allocatedBusId": null,
  "allocatedSeatId": null
}
```

### Response Fields
| Field           | Type    | Description                                                      |
|-----------------|---------|------------------------------------------------------------------|
| id              | string  | Request UUID                                                     |
| date            | string  | Date of the request (YYYY-MM-DD)                                 |
| location        | object  | Pickup location {lat: number, lng: number}                       |
| isDefaultDay    | boolean | true = day is in user's default schedule, false = extra day      |
| isModified      | boolean | true = user changed location from default (MEDIUM priority)      |
| status          | string  | "PENDING" / "ALLOCATED" / "FAILED"                               |
| allocatedBusId  | string  | Bus UUID (null before allocation runs)                           |
| allocatedSeatId | string  | Seat UUID (null before allocation runs)                          |

### Error Responses

**404 Not Found** - No request exists for this date
```json
{
  "detail": "No request found for 2026-01-15. System will auto-create at 10 PM if this is a default day."
}
```

### cURL Example
```bash
curl http://localhost:8000/user/9e7f19d3-a7f8-45f8-a62f-028bb9e6c562/request/2026-01-15
```

### Frontend Usage (TypeScript/JavaScript)
```typescript
async function getDailyRequest(userId: string, date: string) {
  const response = await fetch(
    `http://localhost:8000/user/${userId}/request/${date}`
  );
  
  if (response.ok) {
    const request = await response.json();
    return {
      success: true,
      data: request
    };
  } else if (response.status === 404) {
    return {
      success: false,
      error: 'NO_REQUEST',
      message: 'No request exists for this date'
    };
  } else {
    return {
      success: false,
      error: 'UNKNOWN',
      message: await response.text()
    };
  }
}

// Usage
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const dateStr = tomorrow.toISOString().split('T')[0]; // "2026-01-15"

const result = await getDailyRequest(userId, dateStr);
if (result.success) {
  console.log('Request found:', result.data);
  // Show modify button in UI
} else if (result.error === 'NO_REQUEST') {
  console.log('No request for this date');
  // Hide modify button
}
```

---

## 2. Update Daily Request Location

**Purpose**: Modify the pickup location for an existing request. Used when user wants different pickup point than their default home location.

### Endpoint
```
PUT /user/{userId}/request/{date}
```

### Path Parameters
| Parameter | Type   | Description                           |
|-----------|--------|---------------------------------------|
| userId    | string | User UUID                             |
| date      | string | Date in YYYY-MM-DD format (e.g., 2026-01-15) |

### Request Headers
```
Content-Type: application/json
```

### Request Body
```json
{
  "location": {
    "lat": 12.82,
    "lng": 80.24
  }
}
```

### Request Body Fields
| Field    | Type   | Required | Description                    |
|----------|--------|----------|--------------------------------|
| location | object | Yes      | New pickup location            |
| location.lat | number | Yes  | Latitude (-90 to 90)           |
| location.lng | number | Yes  | Longitude (-180 to 180)        |

### Success Response (200 OK)
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "date": "2026-01-15",
  "location": {
    "lat": 12.82,
    "lng": 80.24
  },
  "isDefaultDay": true,
  "isModified": true,
  "status": "PENDING",
  "allocatedBusId": null,
  "allocatedSeatId": null
}
```

**Note**: After update, `isModified` will be `true` if location differs from user's home location by more than 0.0001 degrees (~11 meters). This changes priority from HIGH to MEDIUM.

### Error Responses

**400 Bad Request** - Deadline passed (after 10 PM the day before)
```json
{
  "detail": "Cannot modify request for 2026-01-15. Deadline passed (10 PM the day before)."
}
```

**404 Not Found** - No request exists
```json
{
  "detail": "No request found for 2026-01-15. Cannot modify a non-existent request."
}
```

**400 Bad Request** - Already allocated
```json
{
  "detail": "Cannot modify an already allocated request."
}
```

### cURL Example
```bash
curl -X PUT http://localhost:8000/user/9e7f19d3-a7f8-45f8-a62f-028bb9e6c562/request/2026-01-15 \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "lat": 12.82,
      "lng": 80.24
    }
  }'
```

### Frontend Usage (TypeScript/JavaScript)
```typescript
interface Location {
  lat: number;
  lng: number;
}

async function updateRequestLocation(
  userId: string, 
  date: string, 
  location: Location
) {
  const response = await fetch(
    `http://localhost:8000/user/${userId}/request/${date}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ location })
    }
  );
  
  if (response.ok) {
    const updated = await response.json();
    return {
      success: true,
      data: updated,
      message: updated.isModified 
        ? 'Location updated (Medium priority)' 
        : 'Location updated'
    };
  } else if (response.status === 400) {
    const error = await response.json();
    return {
      success: false,
      error: 'DEADLINE_PASSED',
      message: error.detail
    };
  } else if (response.status === 404) {
    return {
      success: false,
      error: 'NO_REQUEST',
      message: 'No request exists for this date'
    };
  } else {
    return {
      success: false,
      error: 'UNKNOWN',
      message: await response.text()
    };
  }
}

// Usage Example
const result = await updateRequestLocation(
  userId,
  '2026-01-15',
  { lat: 12.82, lng: 80.24 }
);

if (result.success) {
  console.log('✓ Location updated:', result.data.location);
  if (result.data.isModified) {
    showToast('Location updated! Priority changed to Medium.');
  }
  // Refetch to update UI
  await getDailyRequest(userId, '2026-01-15');
} else if (result.error === 'DEADLINE_PASSED') {
  showAlert('Cannot modify after 10 PM deadline!');
} else {
  showAlert('Update failed: ' + result.message);
}
```

---

## 3. Get All User Requests

**Purpose**: Fetch all upcoming requests for displaying in a list view.

### Endpoint
```
GET /user/{userId}/requests
```

### Path Parameters
| Parameter | Type   | Description |
|-----------|--------|-------------|
| userId    | string | User UUID   |

### Success Response (200 OK)
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "date": "2026-01-15",
    "location": {
      "lat": 12.805748807464756,
      "lng": 80.22034842520952
    },
    "isDefaultDay": true,
    "isModified": false,
    "status": "PENDING",
    "allocatedBusId": null,
    "allocatedSeatId": null
  },
  {
    "id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
    "date": "2026-01-16",
    "location": {
      "lat": 12.82,
      "lng": 80.24
    },
    "isDefaultDay": true,
    "isModified": true,
    "status": "ALLOCATED",
    "allocatedBusId": "c3d4e5f6-g7h8-9012-cdef-123456789012",
    "allocatedSeatId": "d4e5f6g7-h8i9-0123-defg-234567890123"
  }
]
```

### cURL Example
```bash
curl http://localhost:8000/user/9e7f19d3-a7f8-45f8-a62f-028bb9e6c562/requests
```

### Frontend Usage
```typescript
async function getAllRequests(userId: string) {
  const response = await fetch(
    `http://localhost:8000/user/${userId}/requests`
  );
  return response.ok ? await response.json() : [];
}

// Usage - Display in list
const requests = await getAllRequests(userId);
requests.forEach(req => {
  console.log(`${req.date}: ${req.status}`);
  if (req.isModified) {
    console.log('  ⚠️ Modified (Medium priority)');
  }
});
```

---

## 4. Get Allocation Status (Check Result)

**Purpose**: Check if a seat has been allocated for a date (call after 10 PM).

### Endpoint
```
GET /user/{userId}/allocation/{date}
```

### Path Parameters
| Parameter | Type   | Description                           |
|-----------|--------|---------------------------------------|
| userId    | string | User UUID                             |
| date      | string | Date in YYYY-MM-DD format             |

### Success Response (200 OK)

**When Allocated:**
```json
{
  "date": "2026-01-15",
  "status": "ALLOCATED",
  "busId": "c3d4e5f6-g7h8-9012-cdef-123456789012",
  "seatId": "d4e5f6g7-h8i9-0123-defg-234567890123",
  "seatNumber": "A1",
  "message": "Seat allocated successfully!"
}
```

**When Pending:**
```json
{
  "date": "2026-01-15",
  "status": "PENDING",
  "busId": null,
  "seatId": null,
  "seatNumber": null,
  "message": "Allocation pending. Check after 10 PM."
}
```

**When No Request:**
```json
{
  "date": "2026-01-15",
  "status": "NO_REQUEST",
  "busId": null,
  "seatId": null,
  "seatNumber": null,
  "message": "No shuttle request found for this date"
}
```

**When Failed:**
```json
{
  "date": "2026-01-15",
  "status": "FAILED",
  "busId": null,
  "seatId": null,
  "seatNumber": null,
  "message": "Could not allocate seat. All buses full or no suitable route."
}
```

### Frontend Usage
```typescript
async function checkAllocation(userId: string, date: string) {
  const response = await fetch(
    `http://localhost:8000/user/${userId}/allocation/${date}`
  );
  const allocation = await response.json();
  
  switch (allocation.status) {
    case 'ALLOCATED':
      console.log(`✓ Seat ${allocation.seatNumber} allocated`);
      // Show success UI with bus details
      return {
        allocated: true,
        seat: allocation.seatNumber,
        busId: allocation.busId
      };
      
    case 'PENDING':
      console.log('⏳ Allocation not yet run');
      // Show "Check back after 10 PM" message
      return { allocated: false, pending: true };
      
    case 'FAILED':
      console.log('❌ Allocation failed');
      // Show error message, suggest trying different location
      return { allocated: false, failed: true };
      
    case 'NO_REQUEST':
      console.log('ℹ No request for this date');
      // Show "No request" message
      return { allocated: false, noRequest: true };
  }
}

// Usage - Check after 10 PM
const result = await checkAllocation(userId, '2026-01-15');
if (result.allocated) {
  showSuccessScreen(`Your seat: ${result.seat}`);
}
```

---

## Complete Frontend Flow Example

```typescript
// 1. On app load - check tomorrow's request
async function loadTomorrowRequest(userId: string) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dateStr = tomorrow.toISOString().split('T')[0];
  
  const result = await getDailyRequest(userId, dateStr);
  
  if (result.success) {
    // Request exists - show details
    displayRequest(result.data);
    
    // Show modify button if not locked
    const now = new Date();
    const isBeforeDeadline = now.getHours() < 22; // Before 10 PM
    
    if (result.data.status === 'PENDING' && isBeforeDeadline) {
      showModifyButton();
    }
  } else {
    // No request - hide modify button
    hideModifyButton();
    showMessage('No shuttle request for tomorrow');
  }
}

// 2. When user clicks "Modify Location"
async function handleModifyLocation(userId: string, date: string, newLocation: Location) {
  // Show loading
  showLoading('Updating location...');
  
  const result = await updateRequestLocation(userId, date, newLocation);
  
  hideLoading();
  
  if (result.success) {
    // Success - refetch to update UI
    showToast('✓ Location updated!');
    await loadTomorrowRequest(userId);
    
    if (result.data.isModified) {
      showWarning('Priority changed to Medium (modified location)');
    }
  } else if (result.error === 'DEADLINE_PASSED') {
    showAlert('Cannot modify after 10 PM deadline!');
  } else {
    showAlert('Update failed: ' + result.message);
  }
}

// 3. After 10 PM - check allocation result
async function checkTomorrowAllocation(userId: string) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dateStr = tomorrow.toISOString().split('T')[0];
  
  const allocation = await checkAllocation(userId, dateStr);
  
  if (allocation.allocated) {
    // Fetch bus details
    const busDetails = await fetch(`http://localhost:8000/allocation/bus/${allocation.busId}`);
    const bus = await busDetails.json();
    
    showAllocationSuccess({
      seat: allocation.seat,
      busName: bus.routeName,
      departureTime: bus.departureTime
    });
  }
}
```

---

## Testing with cURL

### Complete Test Sequence

```bash
# 1. Get user ID
USER_ID="9e7f19d3-a7f8-45f8-a62f-028bb9e6c562"
TOMORROW="2026-01-15"

# 2. Check if request exists
curl "http://localhost:8000/user/$USER_ID/request/$TOMORROW"

# 3. Update location (if request exists)
curl -X PUT "http://localhost:8000/user/$USER_ID/request/$TOMORROW" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "lat": 12.82,
      "lng": 80.24
    }
  }'

# 4. Verify update
curl "http://localhost:8000/user/$USER_ID/request/$TOMORROW"

# 5. Get all requests
curl "http://localhost:8000/user/$USER_ID/requests"

# 6. Check allocation (after 10 PM)
curl "http://localhost:8000/user/$USER_ID/allocation/$TOMORROW"
```

---

## Status Code Summary

| Code | Meaning                                      |
|------|----------------------------------------------|
| 200  | Success                                      |
| 400  | Bad request (deadline passed, already allocated) |
| 404  | Not found (no request exists)                |
| 422  | Validation error (invalid input format)      |
| 500  | Server error                                 |

---

## Important Notes

### Timing
- Requests are auto-created at **10 PM the night before**
- Users can modify until **10 PM the same day**
- Allocation runs at **10 PM** and locks the date
- After 10 PM, users can only **view** results, not modify

### Priority System
- **HIGH**: Default location, unmodified (`isModified=false`)
- **MEDIUM**: Default location, modified (`isModified=true`)
- **LOW**: Extra day not in defaults (`isDefaultDay=false`)

### Location Tolerance
- Changes < 0.0001 degrees (~11 meters) are considered "same location"
- Larger changes set `isModified=true` and lower priority to MEDIUM

### Refetching After Updates
Always refetch the request after successful update to get the latest `isModified` flag:
```typescript
// After successful update
await getDailyRequest(userId, date);
```
