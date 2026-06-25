# Remote Database Integration for Smart Traffic Analysis System

This document provides instructions for setting up and using a remote SQL database with the Smart Traffic Analysis System.

## Supported Database Types

The system supports the following database types:

- **SQLite** (default, file-based)
- **MySQL** (client-server)
- **PostgreSQL** (client-server)

## Configuration

Database connection parameters are stored in the `db_config.py` file. You can modify this file to change the default connection settings.

```python
# Database connection parameters
DB_CONFIG = {
    # Database type: 'mysql', 'postgresql', or 'sqlite'
    'db_type': 'mysql',
    
    # Remote database connection parameters (for MySQL or PostgreSQL)
    'host': 'localhost',
    'port': 3306,  # Default MySQL port (use 5432 for PostgreSQL)
    'database': 'traffic_db',
    'user': 'traffic_user',
    'password': 'your_password_here',
    
    # SQLite configuration (used as fallback)
    'sqlite_db': 'traffic.db'
}
```

## Prerequisites

### MySQL

1. Install MySQL Server (https://dev.mysql.com/downloads/mysql/)
2. Create a database and user:

```sql
CREATE DATABASE traffic_db;
CREATE USER 'traffic_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON traffic_db.* TO 'traffic_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Install the Python connector:

```
pip install mysql-connector-python
```

### PostgreSQL

1. Install PostgreSQL Server (https://www.postgresql.org/download/)
2. Create a database and user:

```sql
CREATE DATABASE traffic_db;
CREATE USER traffic_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE traffic_db TO traffic_user;
```

3. Install the Python connector:

```
pip install psycopg2-binary
```

## Running the Application with a Remote Database

You can specify the database connection parameters when running the application:

```
python main.py --db-type mysql --host localhost --port 3306 --database traffic_db --user traffic_user --password your_password_here
```

Or for PostgreSQL:

```
python main.py --db-type postgresql --host localhost --port 5432 --database traffic_db --user traffic_user --password your_password_here
```

## Migrating Data from SQLite to a Remote Database

If you have existing data in the SQLite database, you can migrate it to a remote database using the migration script:

```
python migrate_database.py --sqlite traffic.db --host localhost --port 3306 --database traffic_db --user traffic_user --password your_password_here --type mysql
```

Or for PostgreSQL:

```
python migrate_database.py --sqlite traffic.db --host localhost --port 5432 --database traffic_db --user traffic_user --password your_password_here --type postgresql
```

## Fallback Mechanism

The system includes a fallback mechanism that will automatically switch to SQLite if:

1. The required database connector is not installed
2. The remote database connection fails
3. The database type is not supported

This ensures that the application will always work, even if the remote database is not available.

## Troubleshooting

### Connection Issues

If you encounter connection issues, check the following:

1. Make sure the database server is running
2. Verify that the database and user exist with the correct permissions
3. Check that the host, port, username, and password are correct
4. Ensure that the required Python connector is installed

### Database Errors

If you encounter database errors during operation:

1. Check the console output for error messages
2. Verify that the database schema is correct
3. Make sure the user has the necessary permissions

## Security Considerations

1. **Password Storage**: Avoid storing database passwords in the code. Consider using environment variables or a secure configuration file.
2. **Network Security**: If connecting to a remote database over a network, use SSL/TLS encryption.
3. **User Permissions**: Create a database user with only the necessary permissions for the application.
4. **Connection Pooling**: For production use, consider implementing connection pooling to improve performance and security.
