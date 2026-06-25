import sqlite3
from datetime import datetime
import os
import time

class Database:
    def __init__(self, db_name="traffic.db"):
        # Check if the database file exists
        db_exists = os.path.exists(db_name)

        # Connect to the database with extended timeout to prevent locked database errors
        self.conn = sqlite3.connect(db_name, timeout=30)

        # Enable foreign keys support
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Create a cursor
        self.cursor = self.conn.cursor()

        # Create tables if needed
        self.create_tables()

        # Log connection
        print(f"Connected to database: {db_name}")

        # Initialize database if it's new
        if not db_exists:
            self.initialize_database()

    def create_tables(self):
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

            # Statistics table for daily summaries
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

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            # Continue without raising the error to avoid program termination

    def initialize_database(self):
        """Initialize the database with default data if needed"""
        try:
            # Check if we have any violation types
            self.cursor.execute("SELECT COUNT(*) FROM violations")
            count = self.cursor.fetchone()[0]

            # If database is empty, add some initial data
            if count == 0:
                # We don't need to add any initial data for now
                pass

            self.conn.commit()
        except sqlite3.Error:
            # Ignore errors during initialization
            pass

    def add_vehicle(self, plate_number, color, speed, vehicle_type="Unknown"):
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
            else:
                # Insert new vehicle
                self.cursor.execute('''
                    INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                    VALUES (?, ?, ?, ?)
                ''', (plate_number, color, speed, vehicle_type))

            self.conn.commit()

            # Update daily statistics
            self.update_statistics()

            return True
        except sqlite3.Error:
            # Ignore database errors to prevent program termination
            return False

    def add_violation(self, plate_number, violation_type, speed, fine_amount):
        try:
            # Get vehicle ID
            self.cursor.execute('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
            vehicle_id = self.cursor.fetchone()

            if not vehicle_id:
                # If vehicle doesn't exist, create it
                self.add_vehicle(plate_number, "Unknown", speed)

                # Get the new vehicle ID
                self.cursor.execute('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
                vehicle_id = self.cursor.fetchone()

            if vehicle_id:
                # Check if this violation already exists (same vehicle, type, and timestamp within 1 minute)
                self.cursor.execute('''
                    SELECT id FROM violations
                    WHERE vehicle_id = ? AND violation_type = ?
                    AND datetime(timestamp) > datetime('now', '-1 minute')
                ''', (vehicle_id[0], violation_type))

                existing_violation = self.cursor.fetchone()

                if not existing_violation:
                    # Add new violation
                    self.cursor.execute('''
                        INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount)
                        VALUES (?, ?, ?, ?)
                    ''', (vehicle_id[0], violation_type, speed, fine_amount))
                    self.conn.commit()

                    # Update daily statistics
                    self.update_statistics()

                return True
            return False
        except sqlite3.Error:
            # Ignore database errors to prevent program termination
            return False

    def get_vehicle_info(self, plate_number):
        try:
            self.cursor.execute('''
                SELECT * FROM vehicles WHERE plate_number = ?
            ''', (plate_number,))
            return self.cursor.fetchone()
        except sqlite3.Error:
            return None

    def get_violations(self, plate_number=None):
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
        except sqlite3.Error:
            return []

    def get_all_vehicles(self):
        try:
            self.cursor.execute('''
                SELECT * FROM vehicles
                ORDER BY timestamp DESC
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error:
            return []

    def update_statistics(self):
        """Update daily statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # Get today's statistics
            self.cursor.execute('''
                SELECT id FROM statistics WHERE date = ?
            ''', (today,))
            stat_id = self.cursor.fetchone()

            # Calculate statistics
            self.cursor.execute('''
                SELECT COUNT(*) FROM vehicles
            ''')
            total_vehicles = self.cursor.fetchone()[0]

            self.cursor.execute('''
                SELECT COUNT(*) FROM violations
            ''')
            total_violations = self.cursor.fetchone()[0]

            self.cursor.execute('''
                SELECT AVG(speed), MAX(speed) FROM vehicles
            ''')
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

            self.conn.commit()
        except sqlite3.Error:
            # Ignore errors during statistics update
            pass

    def get_statistics(self, days=7):
        """Get statistics for the last N days"""
        try:
            self.cursor.execute('''
                SELECT * FROM statistics
                ORDER BY date DESC
                LIMIT ?
            ''', (days,))
            return self.cursor.fetchall()
        except sqlite3.Error:
            return []

    def update_violation_status(self, violation_id, new_status):
        """Update the status of a violation"""
        try:
            self.cursor.execute('''
                UPDATE violations
                SET status = ?
                WHERE id = ?
            ''', (new_status, violation_id))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def close(self):
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except sqlite3.Error:
            pass