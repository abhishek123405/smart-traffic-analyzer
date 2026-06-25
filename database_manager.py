"""
Database manager for the Smart Traffic Analysis System.
Supports multiple database types including SQLite, MySQL, and PostgreSQL.
"""

import os
import sqlite3
from datetime import datetime
import time
import importlib.util
from db_config import DB_CONFIG

# Check if MySQL connector is available
try:
    import importlib.util
    MYSQL_AVAILABLE = importlib.util.find_spec("mysql.connector") is not None
except ImportError:
    MYSQL_AVAILABLE = False

# Check if PostgreSQL connector is available
try:
    POSTGRESQL_AVAILABLE = importlib.util.find_spec("psycopg2") is not None
except ImportError:
    POSTGRESQL_AVAILABLE = False

class DatabaseManager:
    """Database manager that supports multiple database types."""

    def __init__(self, config=None):
        """Initialize database connection using provided configuration."""
        self.config = config or DB_CONFIG
        self.conn = None
        self.cursor = None
        self.db_type = self.config.get('db_type', 'sqlite').lower()

        # Connect to the appropriate database
        self.connect()

        # Create tables if needed
        self.create_tables()

        # Initialize database if it's new
        self.initialize_database()

    def connect(self):
        """Connect to the database based on the configuration."""
        try:
            if self.db_type == 'mysql':
                if not MYSQL_AVAILABLE:
                    print("MySQL connector not available. Falling back to SQLite.")
                    self.db_type = 'sqlite'
                    self.connect_sqlite()
                else:
                    self.connect_mysql()
            elif self.db_type == 'postgresql':
                if not POSTGRESQL_AVAILABLE:
                    print("PostgreSQL connector not available. Falling back to SQLite.")
                    self.db_type = 'sqlite'
                    self.connect_sqlite()
                else:
                    self.connect_postgresql()
            else:
                # Default to SQLite
                self.db_type = 'sqlite'
                self.connect_sqlite()

            print(f"Connected to {self.db_type} database")
        except Exception as e:
            print(f"Error connecting to {self.db_type} database: {str(e)}")
            print("Falling back to SQLite")
            self.db_type = 'sqlite'
            self.connect_sqlite()

    def connect_sqlite(self):
        """Connect to SQLite database."""
        db_name = self.config.get('sqlite_db', 'traffic.db')
        timeout = self.config.get('timeout', 30)

        # Check if the database file exists
        db_exists = os.path.exists(db_name) if db_name != ':memory:' else False

        # Connect to the database
        self.conn = sqlite3.connect(db_name, timeout=timeout)

        # Enable foreign keys support
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Create a cursor
        self.cursor = self.conn.cursor()

    def connect_mysql(self):
        """Connect to MySQL database."""
        import mysql.connector

        self.conn = mysql.connector.connect(
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 3306),
            database=self.config.get('database', 'traffic_db'),
            user=self.config.get('user', 'root'),
            password=self.config.get('password', ''),
            charset=self.config.get('charset', 'utf8mb4'),
            connection_timeout=self.config.get('timeout', 30)
        )

        self.cursor = self.conn.cursor(buffered=True)

    def connect_postgresql(self):
        """Connect to PostgreSQL database."""
        import psycopg2

        self.conn = psycopg2.connect(
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 5432),
            database=self.config.get('database', 'traffic_db'),
            user=self.config.get('user', 'postgres'),
            password=self.config.get('password', ''),
            connect_timeout=self.config.get('timeout', 30)
        )

        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=None):
        """Execute a query with error handling and reconnection if needed."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                return True
            except (sqlite3.Error, Exception) as e:
                retry_count += 1
                print(f"Database error (attempt {retry_count}/{max_retries}): {str(e)}")

                if retry_count >= max_retries:
                    print("Max retries reached. Query failed.")
                    return False

                # Try to reconnect
                time.sleep(1)
                try:
                    self.connect()
                except Exception as e:
                    print(f"Reconnection failed: {str(e)}")

        return False

    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # Create tables based on database type
            if self.db_type == 'sqlite':
                self.create_tables_sqlite()
            elif self.db_type == 'mysql':
                self.create_tables_mysql()
            elif self.db_type == 'postgresql':
                self.create_tables_postgresql()

            self.conn.commit()
        except Exception as e:
            print(f"Error creating tables: {str(e)}")

    def create_tables_sqlite(self):
        """Create tables for SQLite database."""
        # Check if vehicles table exists
        self.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        table_exists = self.cursor.fetchone() is not None

        if table_exists:
            # Check if vehicle_type column exists
            try:
                self.execute_query("SELECT vehicle_type FROM vehicles LIMIT 1")
                # Column exists, no need to alter table
            except sqlite3.Error:
                # Add vehicle_type column if it doesn't exist
                try:
                    self.execute_query("ALTER TABLE vehicles ADD COLUMN vehicle_type TEXT DEFAULT 'Unknown'")
                    print("Added vehicle_type column to vehicles table")
                except sqlite3.Error as e:
                    print(f"Error adding vehicle_type column: {str(e)}")
        else:
            # Create vehicles table if it doesn't exist
            self.execute_query('''
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
        self.execute_query('''
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
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_vehicles INTEGER DEFAULT 0,
                total_violations INTEGER DEFAULT 0,
                avg_speed REAL DEFAULT 0,
                max_speed INTEGER DEFAULT 0
            )
        ''')

    def create_tables_mysql(self):
        """Create tables for MySQL database."""
        # Vehicles table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plate_number VARCHAR(20) UNIQUE NOT NULL,
                color VARCHAR(20),
                speed INT,
                vehicle_type VARCHAR(20) DEFAULT 'Unknown',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Violations table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS violations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vehicle_id INT,
                violation_type VARCHAR(50) NOT NULL,
                speed INT,
                fine_amount DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'Pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
            )
        ''')

        # Statistics table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                total_vehicles INT DEFAULT 0,
                total_violations INT DEFAULT 0,
                avg_speed DECIMAL(5, 2) DEFAULT 0,
                max_speed INT DEFAULT 0
            )
        ''')

    def create_tables_postgresql(self):
        """Create tables for PostgreSQL database."""
        # Vehicles table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id SERIAL PRIMARY KEY,
                plate_number VARCHAR(20) UNIQUE NOT NULL,
                color VARCHAR(20),
                speed INTEGER,
                vehicle_type VARCHAR(20) DEFAULT 'Unknown',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Violations table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS violations (
                id SERIAL PRIMARY KEY,
                vehicle_id INTEGER,
                violation_type VARCHAR(50) NOT NULL,
                speed INTEGER,
                fine_amount DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'Pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
            )
        ''')

        # Statistics table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS statistics (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                total_vehicles INTEGER DEFAULT 0,
                total_violations INTEGER DEFAULT 0,
                avg_speed DECIMAL(5, 2) DEFAULT 0,
                max_speed INTEGER DEFAULT 0
            )
        ''')

    def initialize_database(self):
        """Initialize the database with default data if needed."""
        try:
            # Check if we have any violation types
            self.execute_query("SELECT COUNT(*) FROM violations")
            count = self.cursor.fetchone()[0]

            # If database is empty, add some initial data
            if count == 0:
                # We don't need to add any initial data for now
                pass

            self.conn.commit()
        except Exception:
            # Ignore errors during initialization
            pass

    def add_vehicle(self, plate_number, color, speed, vehicle_type="Unknown"):
        """Add or update a vehicle in the database."""
        try:
            # Check if vehicle already exists
            if self.db_type == 'sqlite':
                self.execute_query('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
            else:
                self.execute_query('SELECT id FROM vehicles WHERE plate_number = %s', (plate_number,))
            existing_vehicle = self.cursor.fetchone()

            if existing_vehicle:
                # Update existing vehicle
                if self.db_type == 'sqlite':
                    try:
                        # Try with vehicle_type column
                        self.execute_query('''
                            UPDATE vehicles
                            SET color = ?, speed = ?, vehicle_type = ?, timestamp = CURRENT_TIMESTAMP
                            WHERE plate_number = ?
                        ''', (color, speed, vehicle_type, plate_number))
                    except sqlite3.Error:
                        # Fall back to without vehicle_type column
                        self.execute_query('''
                            UPDATE vehicles
                            SET color = ?, speed = ?, timestamp = CURRENT_TIMESTAMP
                            WHERE plate_number = ?
                        ''', (color, speed, plate_number))
                else:
                    self.execute_query('''
                        UPDATE vehicles
                        SET color = %s, speed = %s, vehicle_type = %s, timestamp = CURRENT_TIMESTAMP
                        WHERE plate_number = %s
                    ''', (color, speed, vehicle_type, plate_number))
            else:
                # Insert new vehicle
                if self.db_type == 'sqlite':
                    try:
                        # Try with vehicle_type column
                        self.execute_query('''
                            INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                            VALUES (?, ?, ?, ?)
                        ''', (plate_number, color, speed, vehicle_type))
                    except sqlite3.Error:
                        # Fall back to without vehicle_type column
                        self.execute_query('''
                            INSERT INTO vehicles (plate_number, color, speed)
                            VALUES (?, ?, ?)
                        ''', (plate_number, color, speed))
                else:
                    self.execute_query('''
                        INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                        VALUES (%s, %s, %s, %s)
                    ''', (plate_number, color, speed, vehicle_type))

            self.conn.commit()

            # Update daily statistics
            self.update_statistics()

            return True
        except Exception as e:
            print(f"Error adding vehicle: {str(e)}")
            return False

    def add_violation(self, plate_number, violation_type, speed, fine_amount):
        """Add a violation to the database."""
        try:
            # Get vehicle ID
            if self.db_type == 'sqlite':
                self.execute_query('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
            else:
                self.execute_query('SELECT id FROM vehicles WHERE plate_number = %s', (plate_number,))

            vehicle_id = self.cursor.fetchone()

            if not vehicle_id:
                # If vehicle doesn't exist, create it
                self.add_vehicle(plate_number, "Unknown", speed)

                # Get the new vehicle ID
                if self.db_type == 'sqlite':
                    self.execute_query('SELECT id FROM vehicles WHERE plate_number = ?', (plate_number,))
                else:
                    self.execute_query('SELECT id FROM vehicles WHERE plate_number = %s', (plate_number,))

                vehicle_id = self.cursor.fetchone()

            if vehicle_id:
                # Check if this violation already exists (same vehicle, type, and timestamp within 1 minute)
                if self.db_type == 'sqlite':
                    self.execute_query('''
                        SELECT id FROM violations
                        WHERE vehicle_id = ? AND violation_type = ?
                        AND datetime(timestamp) > datetime('now', '-1 minute')
                    ''', (vehicle_id[0], violation_type))
                elif self.db_type == 'mysql':
                    self.execute_query('''
                        SELECT id FROM violations
                        WHERE vehicle_id = %s AND violation_type = %s
                        AND timestamp > DATE_SUB(NOW(), INTERVAL 1 MINUTE)
                    ''', (vehicle_id[0], violation_type))
                else:  # PostgreSQL
                    self.execute_query('''
                        SELECT id FROM violations
                        WHERE vehicle_id = %s AND violation_type = %s
                        AND timestamp > NOW() - INTERVAL '1 minute'
                    ''', (vehicle_id[0], violation_type))

                existing_violation = self.cursor.fetchone()

                if not existing_violation:
                    # Add new violation
                    if self.db_type == 'sqlite':
                        self.execute_query('''
                            INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount)
                            VALUES (?, ?, ?, ?)
                        ''', (vehicle_id[0], violation_type, speed, fine_amount))
                    else:
                        self.execute_query('''
                            INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount)
                            VALUES (%s, %s, %s, %s)
                        ''', (vehicle_id[0], violation_type, speed, fine_amount))

                    self.conn.commit()

                    # Update daily statistics
                    self.update_statistics()

                return True
            return False
        except Exception as e:
            print(f"Error adding violation: {str(e)}")
            return False

    def get_vehicle_info(self, plate_number):
        """Get vehicle information by plate number."""
        try:
            if self.db_type == 'sqlite':
                self.execute_query('SELECT * FROM vehicles WHERE plate_number = ?', (plate_number,))
            else:
                self.execute_query('SELECT * FROM vehicles WHERE plate_number = %s', (plate_number,))

            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error getting vehicle info: {str(e)}")
            return None

    def get_violations(self, plate_number=None):
        """Get violations with optional filtering by plate number."""
        try:
            if plate_number:
                if self.db_type == 'sqlite':
                    self.execute_query('''
                        SELECT v.*, vh.plate_number, vh.color
                        FROM violations v
                        JOIN vehicles vh ON v.vehicle_id = vh.id
                        WHERE vh.plate_number = ?
                        ORDER BY v.timestamp DESC
                    ''', (plate_number,))
                else:
                    self.execute_query('''
                        SELECT v.*, vh.plate_number, vh.color
                        FROM violations v
                        JOIN vehicles vh ON v.vehicle_id = vh.id
                        WHERE vh.plate_number = %s
                        ORDER BY v.timestamp DESC
                    ''', (plate_number,))
            else:
                self.execute_query('''
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
            self.execute_query('''
                SELECT * FROM vehicles
                ORDER BY timestamp DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting all vehicles: {str(e)}")
            return []

    def update_statistics(self):
        """Update daily statistics."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # Get today's statistics
            if self.db_type == 'sqlite':
                self.execute_query('SELECT id FROM statistics WHERE date = ?', (today,))
            else:
                self.execute_query('SELECT id FROM statistics WHERE date = %s', (today,))

            stat_id = self.cursor.fetchone()

            # Calculate statistics
            self.execute_query('SELECT COUNT(*) FROM vehicles')
            total_vehicles = self.cursor.fetchone()[0]

            self.execute_query('SELECT COUNT(*) FROM violations')
            total_violations = self.cursor.fetchone()[0]

            self.execute_query('SELECT AVG(speed), MAX(speed) FROM vehicles')
            result = self.cursor.fetchone()
            avg_speed = result[0] or 0
            max_speed = result[1] or 0

            if stat_id:
                # Update existing statistics
                if self.db_type == 'sqlite':
                    self.execute_query('''
                        UPDATE statistics
                        SET total_vehicles = ?, total_violations = ?, avg_speed = ?, max_speed = ?
                        WHERE date = ?
                    ''', (total_vehicles, total_violations, avg_speed, max_speed, today))
                else:
                    self.execute_query('''
                        UPDATE statistics
                        SET total_vehicles = %s, total_violations = %s, avg_speed = %s, max_speed = %s
                        WHERE date = %s
                    ''', (total_vehicles, total_violations, avg_speed, max_speed, today))
            else:
                # Insert new statistics
                if self.db_type == 'sqlite':
                    self.execute_query('''
                        INSERT INTO statistics (date, total_vehicles, total_violations, avg_speed, max_speed)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (today, total_vehicles, total_violations, avg_speed, max_speed))
                else:
                    self.execute_query('''
                        INSERT INTO statistics (date, total_vehicles, total_violations, avg_speed, max_speed)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (today, total_vehicles, total_violations, avg_speed, max_speed))

            self.conn.commit()
        except Exception as e:
            print(f"Error updating statistics: {str(e)}")

    def get_statistics(self, days=7):
        """Get statistics for the last N days."""
        try:
            if self.db_type == 'sqlite':
                self.execute_query('''
                    SELECT * FROM statistics
                    ORDER BY date DESC
                    LIMIT ?
                ''', (days,))
            else:
                self.execute_query('''
                    SELECT * FROM statistics
                    ORDER BY date DESC
                    LIMIT %s
                ''', (days,))

            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting statistics: {str(e)}")
            return []

    def update_violation_status(self, violation_id, new_status):
        """Update the status of a violation."""
        try:
            if self.db_type == 'sqlite':
                self.execute_query('''
                    UPDATE violations
                    SET status = ?
                    WHERE id = ?
                ''', (new_status, violation_id))
            else:
                self.execute_query('''
                    UPDATE violations
                    SET status = %s
                    WHERE id = %s
                ''', (new_status, violation_id))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating violation status: {str(e)}")
            return False

    def close(self):
        """Close the database connection."""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                print("Database connection closed")
        except Exception as e:
            print(f"Error closing database connection: {str(e)}")
