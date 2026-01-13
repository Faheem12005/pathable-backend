"""
Seat Allocation Engine - Automated Nightly Processing

This module handles the daily 10 PM seat allocation process:
1. Auto-creates DailyRequest records from user defaults
2. Processes groups with adjacent seating
3. Allocates individuals by priority
4. Records allocation run metadata

Structure allows for future route optimization plugins.
"""
from datetime import date, timedelta, datetime
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.dailyRequest import DailyRequest
from app.models.user import User
from app.models.group import Group
from app.models.groupMember import GroupMember
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.route import Route
from app.models.booking import Booking
from app.models.allocationRun import AllocationRun
import uuid


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_day_abbreviation(target_date: date) -> str:
    """Convert date to day abbreviation (MON, TUE, etc.)"""
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    return days[target_date.weekday()]


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Simple Euclidean distance - replace with proper geo distance later"""
    return ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5


# ============================================
# STEP 1: AUTO-CREATE REQUESTS FROM DEFAULTS
# ============================================

def auto_create_default_requests(db: Session, target_date: date) -> int:
    """
    Create DailyRequest records for users who need shuttle on target_date
    based on their default_days, but ONLY if they haven't already created
    a request (manual modification takes precedence).
    
    Returns: number of auto-created requests
    """
    print(f"🔹 Auto-creating requests from user defaults for {target_date}")
    
    day_abbr = get_day_abbreviation(target_date)
    
    # Find all users who have this day in their default_days
    users_needing_shuttle = (
        db.query(User)
        .filter(User.default_days.contains([day_abbr]))
        .all()
    )
    
    created_count = 0
    
    for user in users_needing_shuttle:
        # Check if user already has a request for this date
        existing = (
            db.query(DailyRequest)
            .filter(and_(
                DailyRequest.user_id == user.id,
                DailyRequest.date == target_date
            ))
            .first()
        )
        
        if existing:
            continue  # User already has a request (manual override)
        
        # Create default request using user's home location
        request = DailyRequest(
            id=uuid.uuid4(),
            user_id=user.id,
            date=target_date,
            request_lat=user.home_lat,
            request_lng=user.home_lng,
            is_default_day=True,
            is_modified=False,  # Using unmodified defaults = HIGH priority
            status="PENDING"
        )
        db.add(request)
        created_count += 1
    
    db.commit()
    print(f"   ✓ Created {created_count} default requests")
    return created_count


# ============================================
# STEP 2: BUS ASSIGNMENT (ROUTE OPTIMIZATION PLACEHOLDER)
# ============================================

def find_best_bus_for_location(db: Session, lat: float, lng: float) -> Bus:
    """
    Find the optimal bus for a given pickup location.
    
    CURRENT: Simple closest-route-endpoint matching
    TODO: Replace with proper route optimization algorithm
          - TSP/VRP solver
          - Dynamic route generation
          - Real-time traffic consideration
    """
    buses = db.query(Bus).all()
    
    if not buses:
        raise Exception("No buses available")
    
    best_bus = None
    min_distance = float('inf')
    
    for bus in buses:
        route = db.query(Route).filter(Route.id == bus.route_id).first()
        if route:
            distance = calculate_distance(lat, lng, route.end_lat, route.end_lng)
            if distance < min_distance:
                min_distance = distance
                best_bus = bus
    
    return best_bus


# ============================================
# STEP 3: SEAT ALLOCATION FUNCTIONS
# ============================================

def get_available_seat(db: Session, bus_id: str) -> Seat:
    """Get the first available seat on a bus"""
    seat = (
        db.query(Seat)
        .filter(and_(Seat.bus_id == bus_id, Seat.is_available == True))
        .order_by(Seat.seat_number)
        .first()
    )
    return seat


def allocate_group_seats(db: Session, group_id: str, target_date: date) -> List[DailyRequest]:
    """
    Allocate adjacent seats for all group members.
    Returns list of allocated requests or raises exception.
    """
    # Get all group members' requests for this date
    member_requests = (
        db.query(DailyRequest, GroupMember)
        .join(GroupMember, DailyRequest.user_id == GroupMember.user_id)
        .filter(and_(
            GroupMember.group_id == group_id,
            DailyRequest.date == target_date,
            DailyRequest.status == "PENDING"
        ))
        .all()
    )
    
    if not member_requests:
        return []
    
    requests = [req for req, _ in member_requests]
    group_size = len(requests)
    
    # Use first member's location to find best bus
    first_req = requests[0]
    best_bus = find_best_bus_for_location(db, first_req.request_lat, first_req.request_lng)
    
    # Try to find adjacent seats
    all_seats = (
        db.query(Seat)
        .filter(and_(Seat.bus_id == best_bus.id, Seat.is_available == True))
        .order_by(Seat.seat_number)
        .all()
    )
    
    if len(all_seats) < group_size:
        raise Exception(f"Not enough seats for group (need {group_size}, have {len(all_seats)})")
    
    # Simple adjacency: just take first N available seats
    # TODO: Better adjacency logic based on seat layout
    selected_seats = all_seats[:group_size]
    
    # Allocate
    for request, seat in zip(requests, selected_seats):
        seat.is_available = False
        request.allocated_bus_id = best_bus.id
        request.allocated_seat_id = seat.id
        request.status = "ALLOCATED"
        
        # Create booking record
        booking = Booking(
            id=uuid.uuid4(),
            user_id=request.user_id,
            bus_id=best_bus.id,
            seat_id=seat.id,
            date=target_date,
            status="CONFIRMED"
        )
        db.add(booking)
    
    return requests


def allocate_individual_request(db: Session, request: DailyRequest, target_date: date) -> bool:
    """
    Allocate a single request based on location.
    Returns True if successful, False if no seats available.
    """
    # Find best bus for user's location
    try:
        best_bus = find_best_bus_for_location(db, request.request_lat, request.request_lng)
    except Exception:
        request.status = "FAILED"
        return False
    
    # Get available seat
    seat = get_available_seat(db, str(best_bus.id))
    
    if not seat:
        # Try other buses if primary is full
        all_buses = db.query(Bus).filter(Bus.id != best_bus.id).all()
        for backup_bus in all_buses:
            seat = get_available_seat(db, str(backup_bus.id))
            if seat:
                best_bus = backup_bus
                break
    
    if not seat:
        request.status = "FAILED"
        return False
    
    # Allocate
    seat.is_available = False
    request.allocated_bus_id = best_bus.id
    request.allocated_seat_id = seat.id
    request.status = "ALLOCATED"
    
    # Create booking record
    booking = Booking(
        id=uuid.uuid4(),
        user_id=request.user_id,
        bus_id=best_bus.id,
        seat_id=seat.id,
        date=target_date,
        status="CONFIRMED"
    )
    db.add(booking)
    
    return True


def run_daily_allocation(db: Session, target_date: date = None) -> Dict:
    """
    MAIN NIGHTLY ALLOCATION PROCESS
    
    Runs the complete seat allocation for a given date:
    1. Auto-create requests from user defaults
    2. Process groups with adjacent seating
    3. Allocate individuals by priority
    4. Record run metadata in allocation_runs table
    
    This function is designed to be called by:
    - Manual trigger (testing/admin)
    - Scheduled cron job (10 PM daily)
    - APScheduler task
    
    Returns: Statistics dict
    """
    if target_date is None:
        target_date = date.today() + timedelta(days=1)  # Tomorrow
    
    # Check if allocation already ran for this date
    existing_run = db.query(AllocationRun).filter(AllocationRun.run_date == target_date).first()
    if existing_run:
        print(f"⚠️  Allocation already ran for {target_date}")
        print(f"   Status: {existing_run.status}")
        print(f"   Executed at: {existing_run.executed_at}")
        return {
            "date": str(target_date),
            "total_requests": existing_run.total_requests,
            "groups_allocated": existing_run.groups_allocated,
            "high_priority_allocated": existing_run.high_priority_allocated,
            "medium_priority_allocated": existing_run.medium_priority_allocated,
            "low_priority_allocated": existing_run.low_priority_allocated,
            "failed": existing_run.failed_allocations,
            "message": "Allocation already completed for this date"
        }
    
    # Create allocation run record
    allocation_run = AllocationRun(
        id=uuid.uuid4(),
        run_date=target_date,
        executed_at=datetime.utcnow(),
        status="RUNNING"
    )
    db.add(allocation_run)
    db.commit()
    
    print(f"\n{'='*60}")
    print(f"🚀 ALLOCATION RUN ID: {allocation_run.id}")
    print(f"📅 DATE: {target_date}")
    print(f"⏰ TIME: {allocation_run.executed_at}")
    print(f"{'='*60}\n")
    
    try:
        # ========================================
        # STEP 1: Auto-create default requests
        # ========================================
        auto_created = auto_create_default_requests(db, target_date)
        
        # ========================================
        # STEP 2: Get all pending requests
        # ========================================
        all_requests = (
            db.query(DailyRequest)
            .filter(and_(
                DailyRequest.date == target_date,
                DailyRequest.status == "PENDING"
            ))
            .all()
        )
        
        allocation_run.total_requests = len(all_requests)
        print(f"📊 Total requests: {len(all_requests)} ({auto_created} auto-created)")
        
        if not all_requests:
            print("✓ No requests to process")
            allocation_run.status = "COMPLETED"
            db.commit()
            return {
                "date": str(target_date),
                "total_requests": 0,
                "groups_allocated": 0,
                "high_priority_allocated": 0,
                "medium_priority_allocated": 0,
                "low_priority_allocated": 0,
                "failed": 0
            }
        
        # ========================================
        # STEP 3: Allocate Groups
        # ========================================
        print("\n🔹 PHASE 1: Group Allocations")
        
        groups_to_allocate = set()
        for req in all_requests:
            membership = db.query(GroupMember).filter(GroupMember.user_id == req.user_id).first()
            if membership:
                groups_to_allocate.add(str(membership.group_id))
        
        print(f"   Found {len(groups_to_allocate)} groups")
        
        for group_id in groups_to_allocate:
            try:
                allocated = allocate_group_seats(db, group_id, target_date)
                allocation_run.groups_allocated += 1
                print(f"   ✓ Group {group_id[:8]}... → {len(allocated)} seats")
            except Exception as e:
                print(f"   ✗ Group {group_id[:8]}... → {e}")
        
        db.commit()
        
        # ========================================
        # STEP 4: Individual Allocations by Priority
        # ========================================
        print("\n🔹 PHASE 2: Individual Allocations")
        
        remaining = (
            db.query(DailyRequest)
            .filter(and_(
                DailyRequest.date == target_date,
                DailyRequest.status == "PENDING"
            ))
            .all()
        )
        
        # Separate by priority
        high_priority = [r for r in remaining if r.is_default_day and not r.is_modified]
        medium_priority = [r for r in remaining if r.is_default_day and r.is_modified]
        low_priority = [r for r in remaining if not r.is_default_day]
        
        print(f"   🟢 High priority: {len(high_priority)}")
        print(f"   🟡 Medium priority: {len(medium_priority)}")
        print(f"   🔴 Low priority: {len(low_priority)}")
        
        # Allocate high priority
        for req in high_priority:
            if allocate_individual_request(db, req, target_date):
                allocation_run.high_priority_allocated += 1
            else:
                allocation_run.failed_allocations += 1
        db.commit()
        
        # Allocate medium priority
        for req in medium_priority:
            if allocate_individual_request(db, req, target_date):
                allocation_run.medium_priority_allocated += 1
            else:
                allocation_run.failed_allocations += 1
        db.commit()
        
        # Allocate low priority
        for req in low_priority:
            if allocate_individual_request(db, req, target_date):
                allocation_run.low_priority_allocated += 1
            else:
                allocation_run.failed_allocations += 1
        db.commit()
        
        # ========================================
        # STEP 5: Complete allocation run
        # ========================================
        allocation_run.status = "COMPLETED"
        db.commit()
        
        print(f"\n{'='*60}")
        print("✅ ALLOCATION COMPLETE")
        print(f"{'='*60}")
        print(f"✓ Groups: {allocation_run.groups_allocated}")
        print(f"✓ High Priority: {allocation_run.high_priority_allocated}")
        print(f"✓ Medium Priority: {allocation_run.medium_priority_allocated}")
        print(f"✓ Low Priority: {allocation_run.low_priority_allocated}")
        print(f"✗ Failed: {allocation_run.failed_allocations}")
        print(f"{'='*60}\n")
        
        return {
            "date": str(target_date),
            "total_requests": allocation_run.total_requests,
            "groups_allocated": allocation_run.groups_allocated,
            "high_priority_allocated": allocation_run.high_priority_allocated,
            "medium_priority_allocated": allocation_run.medium_priority_allocated,
            "low_priority_allocated": allocation_run.low_priority_allocated,
            "failed": allocation_run.failed_allocations
        }
    
    except Exception as e:
        # Mark allocation run as failed
        allocation_run.status = "FAILED"
        allocation_run.error_message = str(e)
        db.commit()
        
        print(f"\n❌ ALLOCATION FAILED: {e}\n")
        raise e
