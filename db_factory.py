"""
Database factory for the Smart Traffic Analysis System.
This module provides a factory function to create the appropriate database connection.
"""

import os
import importlib.util
from database_manager import DatabaseManager
from db_config import DB_CONFIG

def create_database(config=None):
    """
    Create a database connection based on configuration.
    
    Args:
        config (dict, optional): Database configuration. Defaults to DB_CONFIG.
    
    Returns:
        DatabaseManager: A database manager instance.
    """
    config = config or DB_CONFIG
    db_type = config.get('db_type', 'sqlite').lower()
    
    # Check if required modules are available
    if db_type == 'mysql':
        if not importlib.util.find_spec("mysql.connector"):
            print("MySQL connector not available. Install with: pip install mysql-connector-python")
            print("Falling back to SQLite")
            config['db_type'] = 'sqlite'
    elif db_type == 'postgresql':
        if not importlib.util.find_spec("psycopg2"):
            print("PostgreSQL connector not available. Install with: pip install psycopg2")
            print("Falling back to SQLite")
            config['db_type'] = 'sqlite'
    
    # Create database manager
    return DatabaseManager(config)
