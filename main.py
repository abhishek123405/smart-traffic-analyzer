import tkinter as tk
import os
import sys
import argparse
from gui import TrafficGUI
from db_factory import create_database
from db_config import DB_CONFIG

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Smart Traffic Analysis System')
    parser.add_argument('--db-type', choices=['sqlite', 'mysql', 'postgresql'],
                        help='Database type to use')
    parser.add_argument('--host', help='Database host (for MySQL/PostgreSQL)')
    parser.add_argument('--port', type=int, help='Database port (for MySQL/PostgreSQL)')
    parser.add_argument('--database', help='Database name (for MySQL/PostgreSQL)')
    parser.add_argument('--user', help='Database user (for MySQL/PostgreSQL)')
    parser.add_argument('--password', help='Database password (for MySQL/PostgreSQL)')

    args = parser.parse_args()

    # Update configuration with command line arguments
    config = DB_CONFIG.copy()
    if args.db_type:
        config['db_type'] = args.db_type
    if args.host:
        config['host'] = args.host
    if args.port:
        config['port'] = args.port
    if args.database:
        config['database'] = args.database
    if args.user:
        config['user'] = args.user
    if args.password:
        config['password'] = args.password

    # Create database connection
    db = create_database(config)

    # Create GUI
    root = tk.Tk()
    app = TrafficGUI(root, db)
    root.mainloop()

    # Close database connection
    db.close()

if __name__ == "__main__":
    main()