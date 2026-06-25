"""
Migration script to transfer data from SQLite to MySQL.
This script will migrate all data from the SQLite database to MySQL.
"""

import os
import sqlite3
import mysql.connector
from datetime import datetime
import time

def migrate_sqlite_to_mysql():
    """Migrate data from SQLite to MySQL."""
    print("Starting migration from SQLite to MySQL...")

    # SQLite connection
    sqlite_db = "traffic.db"
    if not os.path.exists(sqlite_db):
        print(f"SQLite database file not found: {sqlite_db}")
        return False

    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        print(f"Connected to SQLite database: {sqlite_db}")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {str(e)}")
        return False

    # MySQL connection
    try:
        mysql_conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            database="traffic_db",
            user="root",
            password="root"  # Replace with your actual password
        )
        mysql_cursor = mysql_conn.cursor()
        print("Connected to MySQL database")
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL database: {str(e)}")
        sqlite_conn.close()
        return False

    try:
        # Create tables in MySQL
        # Vehicles table
        mysql_cursor.execute('''
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
        mysql_cursor.execute('''
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
        mysql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                total_vehicles INT DEFAULT 0,
                total_violations INT DEFAULT 0,
                avg_speed DECIMAL(5, 2) DEFAULT 0,
                max_speed INT DEFAULT 0
            )
        ''')

        mysql_conn.commit()
        print("Tables created in MySQL database")

        # Check if vehicles table has vehicle_type column in SQLite
        has_vehicle_type = True
        try:
            sqlite_cursor.execute("SELECT vehicle_type FROM vehicles LIMIT 1")
        except sqlite3.Error:
            has_vehicle_type = False
            print("SQLite vehicles table does not have vehicle_type column")

        # Migrate vehicles data
        sqlite_cursor.execute("SELECT * FROM vehicles")
        vehicles = sqlite_cursor.fetchall()

        if vehicles:
            print(f"Migrating {len(vehicles)} vehicles...")

            for vehicle in vehicles:
                # Extract vehicle data
                if has_vehicle_type and len(vehicle) >= 5:
                    id, plate_number, color, speed, vehicle_type = vehicle[:5]
                else:
                    id, plate_number, color, speed = vehicle[:4]
                    vehicle_type = "Unknown"

                # Insert into MySQL
                mysql_cursor.execute('''
                    INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    color = %s, speed = %s, vehicle_type = %s
                ''', (plate_number, color, speed, vehicle_type, color, speed, vehicle_type))

            mysql_conn.commit()
            print("Vehicles data migrated successfully")

        # Migrate violations data
        sqlite_cursor.execute('''
            SELECT v.id, v.vehicle_id, v.violation_type, v.speed, v.fine_amount, v.status, v.timestamp, vh.plate_number
            FROM violations v
            JOIN vehicles vh ON v.vehicle_id = vh.id
        ''')
        violations = sqlite_cursor.fetchall()

        if violations:
            print(f"Migrating {len(violations)} violations...")

            for violation in violations:
                id, vehicle_id, violation_type, speed, fine_amount, status, timestamp, plate_number = violation

                # Get vehicle ID in MySQL
                mysql_cursor.execute('SELECT id FROM vehicles WHERE plate_number = %s', (plate_number,))
                mysql_vehicle = mysql_cursor.fetchone()

                if mysql_vehicle:
                    mysql_vehicle_id = mysql_vehicle[0]

                    # Insert violation
                    mysql_cursor.execute('''
                        INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount, status)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (mysql_vehicle_id, violation_type, speed, fine_amount, status))

            mysql_conn.commit()
            print("Violations data migrated successfully")

        # Migrate statistics data
        sqlite_cursor.execute("SELECT * FROM statistics")
        statistics = sqlite_cursor.fetchall()

        if statistics:
            print(f"Migrating {len(statistics)} statistics records...")

            for stat in statistics:
                id, date, total_vehicles, total_violations, avg_speed, max_speed = stat

                # Insert statistics
                # Limit avg_speed to a reasonable value (MySQL DECIMAL(5,2) has a max of 999.99)
                if avg_speed > 999.99:
                    avg_speed = 999.99

                # Limit max_speed to INT range
                if max_speed > 2147483647:
                    max_speed = 2147483647

                mysql_cursor.execute('''
                    INSERT INTO statistics (date, total_vehicles, total_violations, avg_speed, max_speed)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    total_vehicles = %s, total_violations = %s, avg_speed = %s, max_speed = %s
                ''', (date, total_vehicles, total_violations, avg_speed, max_speed,
                      total_vehicles, total_violations, avg_speed, max_speed))

            mysql_conn.commit()
            print("Statistics data migrated successfully")

        print("Migration completed successfully!")
        return True
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False
    finally:
        # Close connections
        sqlite_conn.close()
        mysql_conn.close()
        print("Database connections closed")

if __name__ == "__main__":
    migrate_sqlite_to_mysql()
