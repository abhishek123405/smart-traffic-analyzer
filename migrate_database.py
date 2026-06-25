"""
Database migration script for the Smart Traffic Analysis System.
This script migrates data from SQLite to a remote SQL database.
"""

import os
import sqlite3
import argparse
import importlib.util
from db_config import DB_CONFIG

def migrate_sqlite_to_remote(sqlite_db='traffic.db', config=None):
    """
    Migrate data from SQLite to a remote SQL database.
    
    Args:
        sqlite_db (str): Path to SQLite database file
        config (dict): Remote database configuration
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    config = config or DB_CONFIG
    db_type = config.get('db_type', '').lower()
    
    if db_type not in ('mysql', 'postgresql'):
        print(f"Unsupported target database type: {db_type}")
        return False
    
    if not os.path.exists(sqlite_db):
        print(f"SQLite database file not found: {sqlite_db}")
        return False
    
    # Connect to SQLite database
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        print(f"Connected to SQLite database: {sqlite_db}")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite database: {str(e)}")
        return False
    
    # Connect to remote database
    try:
        if db_type == 'mysql':
            if not importlib.util.find_spec("mysql.connector"):
                print("MySQL connector not available. Install with: pip install mysql-connector-python")
                return False
            
            import mysql.connector
            remote_conn = mysql.connector.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 3306),
                database=config.get('database', 'traffic_db'),
                user=config.get('user', 'root'),
                password=config.get('password', 'root'),
                charset=config.get('charset', 'utf8mb4')
            )
            remote_cursor = remote_conn.cursor()
            print(f"Connected to MySQL database: {config.get('database')}")
        elif db_type == 'postgresql':
            if not importlib.util.find_spec("psycopg2"):
                print("PostgreSQL connector not available. Install with: pip install psycopg2")
                return False
            
            import psycopg2
            remote_conn = psycopg2.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 5432),
                database=config.get('database', 'traffic_db'),
                user=config.get('user', 'postgres'),
                password=config.get('password', 'root')
            )
            remote_cursor = remote_conn.cursor()
            print(f"Connected to PostgreSQL database: {config.get('database')}")
    except Exception as e:
        print(f"Error connecting to remote database: {str(e)}")
        sqlite_conn.close()
        return False
    
    try:
        # Create tables in remote database
        if db_type == 'mysql':
            # Vehicles table
            remote_cursor.execute('''
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
            remote_cursor.execute('''
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
            remote_cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    total_vehicles INT DEFAULT 0,
                    total_violations INT DEFAULT 0,
                    avg_speed DECIMAL(5, 2) DEFAULT 0,
                    max_speed INT DEFAULT 0
                )
            ''')
        elif db_type == 'postgresql':
            # Vehicles table
            remote_cursor.execute('''
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
            remote_cursor.execute('''
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
            remote_cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id SERIAL PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    total_vehicles INTEGER DEFAULT 0,
                    total_violations INTEGER DEFAULT 0,
                    avg_speed DECIMAL(5, 2) DEFAULT 0,
                    max_speed INTEGER DEFAULT 0
                )
            ''')
        
        remote_conn.commit()
        print("Tables created in remote database")
        
        # Migrate vehicles data
        sqlite_cursor.execute("SELECT * FROM vehicles")
        vehicles = sqlite_cursor.fetchall()
        
        if vehicles:
            print(f"Migrating {len(vehicles)} vehicles...")
            
            for vehicle in vehicles:
                # Check if vehicle_type column exists
                if len(vehicle) >= 5:
                    id, plate_number, color, speed, vehicle_type = vehicle[:5]
                else:
                    id, plate_number, color, speed = vehicle[:4]
                    vehicle_type = "Unknown"
                
                # Insert into remote database
                if db_type == 'mysql':
                    remote_cursor.execute('''
                        INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        color = %s, speed = %s, vehicle_type = %s
                    ''', (plate_number, color, speed, vehicle_type, color, speed, vehicle_type))
                elif db_type == 'postgresql':
                    remote_cursor.execute('''
                        INSERT INTO vehicles (plate_number, color, speed, vehicle_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (plate_number) DO UPDATE SET
                        color = EXCLUDED.color, speed = EXCLUDED.speed, vehicle_type = EXCLUDED.vehicle_type
                    ''', (plate_number, color, speed, vehicle_type))
            
            remote_conn.commit()
            print("Vehicles data migrated successfully")
        
        # Migrate violations data
        sqlite_cursor.execute('''
            SELECT v.id, v.vehicle_id, v.violation_type, v.speed, v.fine_amount, v.status, vh.plate_number
            FROM violations v
            JOIN vehicles vh ON v.vehicle_id = vh.id
        ''')
        violations = sqlite_cursor.fetchall()
        
        if violations:
            print(f"Migrating {len(violations)} violations...")
            
            for violation in violations:
                id, vehicle_id, violation_type, speed, fine_amount, status, plate_number = violation
                
                # Get vehicle ID in remote database
                if db_type == 'mysql':
                    remote_cursor.execute('SELECT id FROM vehicles WHERE plate_number = %s', (plate_number,))
                elif db_type == 'postgresql':
                    remote_cursor.execute('SELECT id FROM vehicles WHERE plate_number = %s', (plate_number,))
                
                remote_vehicle = remote_cursor.fetchone()
                
                if remote_vehicle:
                    remote_vehicle_id = remote_vehicle[0]
                    
                    # Insert violation
                    if db_type == 'mysql':
                        remote_cursor.execute('''
                            INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount, status)
                            VALUES (%s, %s, %s, %s, %s)
                        ''', (remote_vehicle_id, violation_type, speed, fine_amount, status))
                    elif db_type == 'postgresql':
                        remote_cursor.execute('''
                            INSERT INTO violations (vehicle_id, violation_type, speed, fine_amount, status)
                            VALUES (%s, %s, %s, %s, %s)
                        ''', (remote_vehicle_id, violation_type, speed, fine_amount, status))
            
            remote_conn.commit()
            print("Violations data migrated successfully")
        
        # Migrate statistics data
        sqlite_cursor.execute("SELECT * FROM statistics")
        statistics = sqlite_cursor.fetchall()
        
        if statistics:
            print(f"Migrating {len(statistics)} statistics records...")
            
            for stat in statistics:
                id, date, total_vehicles, total_violations, avg_speed, max_speed = stat
                
                # Insert statistics
                if db_type == 'mysql':
                    remote_cursor.execute('''
                        INSERT INTO statistics (date, total_vehicles, total_violations, avg_speed, max_speed)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        total_vehicles = %s, total_violations = %s, avg_speed = %s, max_speed = %s
                    ''', (date, total_vehicles, total_violations, avg_speed, max_speed,
                          total_vehicles, total_violations, avg_speed, max_speed))
                elif db_type == 'postgresql':
                    remote_cursor.execute('''
                        INSERT INTO statistics (date, total_vehicles, total_violations, avg_speed, max_speed)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (date) DO UPDATE SET
                        total_vehicles = EXCLUDED.total_vehicles,
                        total_violations = EXCLUDED.total_violations,
                        avg_speed = EXCLUDED.avg_speed,
                        max_speed = EXCLUDED.max_speed
                    ''', (date, total_vehicles, total_violations, avg_speed, max_speed))
            
            remote_conn.commit()
            print("Statistics data migrated successfully")
        
        print("Migration completed successfully")
        return True
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False
    finally:
        # Close connections
        sqlite_conn.close()
        remote_conn.close()

def main():
    """Main function to run the migration script."""
    parser = argparse.ArgumentParser(description='Migrate data from SQLite to a remote SQL database')
    parser.add_argument('--sqlite', default='traffic.db', help='Path to SQLite database file')
    parser.add_argument('--host', default=DB_CONFIG.get('host', 'localhost'), help='Remote database host')
    parser.add_argument('--port', type=int, default=DB_CONFIG.get('port', 3306), help='Remote database port')
    parser.add_argument('--database', default=DB_CONFIG.get('database', 'traffic_db'), help='Remote database name')
    parser.add_argument('--user', default=DB_CONFIG.get('user', 'root'), help='Remote database user')
    parser.add_argument('--password', default=DB_CONFIG.get('password', 'root'), help='Remote database password')
    parser.add_argument('--type', default=DB_CONFIG.get('db_type', 'mysql'), choices=['mysql', 'postgresql'], help='Remote database type')
    
    args = parser.parse_args()
    
    config = {
        'db_type': args.type,
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': args.password
    }
    
    migrate_sqlite_to_remote(args.sqlite, config)

if __name__ == '__main__':
    main()
