"""
Seed script to populate database with test data for development.
Run with: python scripts/seed_data.py
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.database import SessionLocal
from app.models.route import Route
from app.models.bus import Bus
from app.models.seat import Seat
import uuid


def clear_existing_data(db):
    """Clear existing buses, seats, and routes"""
    print("Clearing existing data...")
    db.query(Seat).delete()
    db.query(Bus).delete()
    db.query(Route).delete()
    db.commit()
    print("✓ Existing data cleared")


def create_routes(db):
    """Create sample routes to common destinations"""
    routes = [
        {
            "poi_name": "VIT Main Campus",
            "end_lat": 12.969195,
            "end_lng": 79.155462
        },
        {
            "poi_name": "Chennai Central",
            "end_lat": 13.082047,
            "end_lng": 80.275116
        }
    ]
    
    route_objects = []
    for route_data in routes:
        route = Route(
            id=uuid.uuid4(),
            poi_name=route_data["poi_name"],
            end_lat=route_data["end_lat"],
            end_lng=route_data["end_lng"]
        )
        db.add(route)
        route_objects.append(route)
    
    db.commit()
    print(f"✓ Created {len(route_objects)} routes")
    return route_objects


def create_buses_and_seats(db, routes):
    """Create 2 buses with 20 seats each"""
    buses = []
    
    for i, route in enumerate(routes[:2], 1):
        bus = Bus(
            id=uuid.uuid4(),
            route_id=route.id,
            capacity=20
        )
        db.add(bus)
        db.flush()  # Get bus.id
        
        # Create 20 seats per bus (4 rows × 5 seats: A-D + window)
        # Format: A1, A2, B1, B2, C1, C2, D1, D2, etc.
        seat_count = 0
        for row in range(1, 6):  # 5 rows
            for col in ['A', 'B', 'C', 'D']:  # 4 columns
                seat_count += 1
                if seat_count > 20:
                    break
                    
                seat = Seat(
                    id=uuid.uuid4(),
                    bus_id=bus.id,
                    seat_number=f"{col}{row}",
                    is_available=True
                )
                db.add(seat)
        
        buses.append(bus)
        print(f"✓ Created Bus {i} with 20 seats on route '{route.poi_name}'")
    
    db.commit()
    return buses


def main():
    print("=" * 60)
    print("SEEDING DATABASE WITH TEST DATA")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clear and seed
        clear_existing_data(db)
        routes = create_routes(db)
        buses = create_buses_and_seats(db, routes)
        
        print("\n" + "=" * 60)
        print("✓ SEEDING COMPLETE")
        print("=" * 60)
        print(f"Created: {len(routes)} routes, {len(buses)} buses, {len(buses) * 20} seats")
        
        # Print bus IDs for testing
        print("\nBus IDs for testing:")
        for i, bus in enumerate(buses, 1):
            route = db.query(Route).filter(Route.id == bus.route_id).first()
            print(f"  Bus {i}: {bus.id} → {route.poi_name}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
