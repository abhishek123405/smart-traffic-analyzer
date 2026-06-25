"""
Simple database connection for the Smart Traffic Analysis System.
This module provides a direct connection to a local SQLite database.
"""

import sqlite3
import os
from datetime import datetime

class SimpleDatabase:
    """A simple database class that uses SQLite for local storage."""
    
    def __init__(self, db_file="traffic_local.db"):
        """Initialize the database connection."""
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """Connect to the SQLite database."""
        try:
            # Check if database file exists
            db_exists = os.path.exists(self.db_file)
            
            # Connect to the database
            self.connection = sqlite3.connect(self.db_file)
            self.cursor = self.connection.cursor()
            
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables if they don't exist
            self.create_tables()
            
            print(f"Connected to local database: {self.db_file}")
            print(f"Database file location: {os.path.abspath(self.db_file)}")
            
            return True
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            return False
    
    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        try:
            # Vehicles table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT UNIQUE NOT NULL,
                    color TEXT,
                    speed INTEGER,
                    vehicle_type TEXT DEFAULT 'Unknown',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Violations table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER,
                    violation_type TEXT NOT NULL,
                    speed INTEGER,
                    fine_amount REAL,
                    status TEXT DEFAULT 'Pending',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            ''')
            
            # Statistics table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_vehicles INTEGER DEFAULT 0,
                    total_violations INTEGER DEFAULT 0,
                    avg_speed REAL DEFAULT 0,
                    max_speed INTEGER DEFAULT 0
                )
            ''')
            
            self.connection.commit()
            print("Database tables created successfully")
            return True
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            return False
    
    def add_vehicle(self, plate_number, color, speed, vehicle_type="Unknown"):
        """Add a vehicle to the database."""
        try:
            # Check if vehicle already exists
            self.cursor.execute('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
            existing_vehicle = self.cursor.fetchone()
            
            if existing_vehicle:
                # Update existing vehicle
                self.cursor.execute('''
                    UPDATE vehicles 
                    SET color = ?, speed = ?, vehicle_type = ?, timestamp = CURRENT_TIMESTAMP 
                    WHERE plate_number = ?
                ''', (color, speed, vehicle_type, plate_number))
                print(f"Updated vehicle: {plate_number}")
            else:
                # Insert new vehicle
                self.cursor.execute('''
                    INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                    VALUES (?, ?, ?, ?)
                ''', (plate_number, color, speed, vehicle_type))
                print(f"Added new vehicle: {plate_number}")
            
            self.connection.commit()
            
            # Update statistics
            self.update_statistics()
            
            return True
        except Exception as e:
            print(f"Error adding vehicle: {str(e)}")
            return False
    
    def add_violation(self, plate_number, violation_type, speed, fine_amount):
        """Add a violation to the database."""
        try:
            # Get vehicle ID
            self.cursor.execute('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
            vehicle = self.cursor.fetchone()
            
            if not vehicle:
                # Create vehicle if it doesn't exist
                self.add_vehicle(plate_number, "Unknown", speed)
                
                # Get the new vehicle ID
                self.cursor.execute('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
                vehicle = self.cursor.fetchone()
            
            if vehicle:
                vehicle_id = vehicle[0]
                
                # Add violation
                self.cursor.execute('''
                    INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount)
                    VALUES (?, ?, ?, ?)
                ''', (vehicle_id, violation_type, speed, fine_amount))
                
                self.connection.commit()
                print(f"Added violation for vehicle: {plate_number}, Type: {violation_type}")
                
                # Update statistics
                self.update_statistics()
                
                return True
            return False
        except Exception as e:
            print(f"Error adding violation: {str(e)}")
            return False
    
    def get_vehicle_info(self, plate_number):
        """Get vehicle information by plate number."""
        try:
            self.cursor.execute('SELECT * FROM vehicles WHERE plate_number = ?', (plate_number,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error getting vehicle info: {str(e)}")
            return None
    
    def get_violations(self, plate_number=None):
        """Get violations with optional filtering by plate number."""
        try:
            if plate_number:
                self.cursor.execute('''
                    SELECT v.*, vh.plate_number, vh.color 
                    FROM violations v
                    JOIN vehicles vh ON v.vehicle_id = vh.id
                    WHERE vh.plate_number = ?
                    ORDER BY v.timestamp DESC
                ''', (plate_number,))
            else:
                self.cursor.execute('''
                    SELECT v.*, vh.plate_number, vh.color 
                    FROM violations v
                    JOIN vehicles vh ON v.vehicle_id = vh.id
                    ORDER BY v.timestamp DESC
                ''')
            
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting violations: {str(e)}")
            return []
    
    def get_all_vehicles(self):
        """Get all vehicles from the database."""
        try:
            self.cursor.execute('SELECT * FROM vehicles ORDER BY timestamp DESC')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting all vehicles: {str(e)}")
            return []
    
    def update_statistics(self):
        """Update daily statistics."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get today's statistics
            self.cursor.execute('SELECT id FROM statistics WHERE date = ?', (today,))
            stat_id = self.cursor.fetchone()
            
            # Calculate statistics
            self.cursor.execute('SELECT COUNT(*) FROM vehicles')
            total_vehicles = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT COUNT(*) FROM violations')
            total_violations = self.cursor.fetchone()[0]
            
            self.cursor.execute('SELECT AVG(speed), MAX(speed) FROM vehicles')
            result = self.cursor.fetchone()
            avg_speed = result[0] or 0
            max_speed = result[1] or 0
            
            if stat_id:
                # Update existing statistics
                self.cursor.execute('''
                    UPDATE statistics
                    SET total_vehicles = ?, total_violations = ?, avg_speed = ?, max_speed = ?
                    WHERE date = ?
                ''', (total_vehicles, total_violations, avg_speed, max_speed, today))
            else:
                # Insert new statistics
                self.cursor.execute('''
                    INSERT INTO statistics (date, total_vehicles, total_violations, avg_speed, max_speed)
                    VALUES (?, ?, ?, ?, ?)
                ''', (today, total_vehicles, total_violations, avg_speed, max_speed))
            
            self.connection.commit()
            print(f"Updated statistics for {today}")
            return True
        except Exception as e:
            print(f"Error updating statistics: {str(e)}")
            return False
    
    def get_statistics(self, days=7):
        """Get statistics for the last N days."""
        try:
            self.cursor.execute('''
                SELECT * FROM statistics
                ORDER BY date DESC
                LIMIT ?
            ''', (days,))
            
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting statistics: {str(e)}")
            return []
    
    def update_violation_status(self, violation_id, new_status):
        """Update the status of a violation."""
        try:
            self.cursor.execute('''
                UPDATE violations
                SET status = ?
                WHERE id = ?
            ''', (new_status, violation_id))
            
            self.connection.commit()
            print(f"Updated violation status: ID {violation_id} -> {new_status}")
            return True
        except Exception as e:
            print(f"Error updating violation status: {str(e)}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
