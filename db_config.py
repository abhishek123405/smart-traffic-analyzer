"""
Database configuration settings for the Smart Traffic Analysis System.
This file contains the connection parameters for the remote SQL database.
"""

# Database connection parameters
DB_CONFIG = {
    # Database type: 'mysql', 'postgresql', or 'sqlite'
    'db_type': 'mysql',

    # Remote database connection parameters (for MySQL or PostgreSQL)
    'host': 'localhost',
    'port': 3306,  # Default MySQL port (use 5432 for PostgreSQL)
    'database': 'traffic_db',
    'user': 'root',
    'password': 'root',  # Replace with your actual password

    # SQLite configuration (used as fallback)
    'sqlite_db': 'traffic.db',

    # Connection settings
    'timeout': 30,
    'charset': 'utf8mb4',

    # Pool settings
    'pool_size': 5,
    'max_overflow': 10
}

# Test connection parameters (for unit tests)
TEST_DB_CONFIG = {
    'db_type': 'sqlite',
    'sqlite_db': ':memory:',
    'timeout': 30
}
