"""
Test script for database connection.
This script tests the database connection and performs basic operations.
"""

import os
from db_factory import create_database
from db_config import DB_CONFIG

def test_database_connection():
    """Test database connection and basic operations."""
    print("Testing database connection...")
    
    # Create database connection
    db = create_database()
    
    # Print database type
    print(f"Connected to {db.db_type} database")
    
    # Test adding a vehicle
    plate_number = "TEST123"
    color = "Red"
    speed = 50
    
    print(f"Adding test vehicle: {plate_number}, {color}, {speed} km/h")
    result = db.add_vehicle(plate_number, color, speed)
    print(f"Result: {result}")
    
    # Test adding a violation
    violation_type = "Speeding"
    fine_amount = 100.0
    
    print(f"Adding test violation: {plate_number}, {violation_type}, {speed} km/h, ${fine_amount}")
    result = db.add_violation(plate_number, violation_type, speed, fine_amount)
    print(f"Result: {result}")
    
    # Test retrieving vehicle info
    print(f"Retrieving vehicle info for {plate_number}")
    vehicle_info = db.get_vehicle_info(plate_number)
    print(f"Vehicle info: {vehicle_info}")
    
    # Test retrieving violations
    print(f"Retrieving violations for {plate_number}")
    violations = db.get_violations(plate_number)
    print(f"Violations: {violations}")
    
    # Test retrieving statistics
    print("Retrieving statistics")
    statistics = db.get_statistics()
    print(f"Statistics: {statistics}")
    
    # Close database connection
    db.close()
    print("Database connection closed")
    
    print("Database test completed successfully!")

if __name__ == "__main__":
    test_database_connection()
