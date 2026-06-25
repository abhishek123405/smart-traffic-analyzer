# Smart Traffic Analysis System - Local Storage

This document provides instructions for using the local storage version of the Smart Traffic Analysis System.

## Overview

The local storage version of the application uses SQLite for database storage. SQLite is a file-based database that stores all data in a single file on your local machine. This makes it easy to use and portable, with no need for a separate database server.

## Database Location

The database file is stored in the root directory of the application:

```
C:\Users\ssraj\OneDrive\Desktop\smart-traffic-analysis\traffic_local.db
```

This file contains all your traffic analysis data, including vehicles, violations, and statistics.

## Using the Application

There are two ways to run the application with local storage:

### 1. Simple Application (Recommended)

The simple application provides a clean interface focused on local storage:

```
python simple_app.py
```

This version:
- Shows the database file location in the window title
- Provides clear feedback about database operations
- Uses a simplified interface focused on the core functionality

### 2. Main Application with Local Storage

The main application can also be run with local storage:

```
python main_local.py
```

This version:
- Uses the full application interface
- Shows database information at the top of the window
- Uses the same local database file

## Viewing the Database

You can view and edit the database directly using:

1. **SQLite Browser**: Download from https://sqlitebrowser.org/
   - Open the `traffic_local.db` file
   - Browse tables, run queries, and edit data

2. **Visual Studio Code with SQLite extension**:
   - Install the SQLite extension
   - Open the `traffic_local.db` file
   - View and edit data directly in VS Code

## Database Structure

The database contains the following tables:

1. **vehicles**: Stores information about vehicles
   - id: Unique identifier
   - plate_number: Vehicle license plate
   - color: Vehicle color
   - speed: Vehicle speed in km/h
   - vehicle_type: Type of vehicle (Car, Truck, etc.)
   - timestamp: When the vehicle was added

2. **violations**: Stores traffic violations
   - id: Unique identifier
   - vehicle_id: Reference to the vehicle
   - violation_type: Type of violation
   - speed: Vehicle speed at time of violation
   - fine_amount: Fine amount for the violation
   - status: Status of the violation (Pending, Paid, etc.)
   - timestamp: When the violation occurred

3. **statistics**: Stores daily statistics
   - id: Unique identifier
   - date: Date of the statistics
   - total_vehicles: Total number of vehicles
   - total_violations: Total number of violations
   - avg_speed: Average speed of vehicles
   - max_speed: Maximum speed recorded

## Backing Up the Database

To back up your data, simply copy the `traffic_local.db` file to another location. For example:

```
copy traffic_local.db backups\traffic_backup_20250422.db
```

## Troubleshooting

If you encounter any issues with the database:

1. **Database file not found**: Make sure you're running the application from the correct directory.

2. **Permission errors**: Ensure you have write permissions for the directory.

3. **Corrupted database**: If the database becomes corrupted, you can delete the `traffic_local.db` file and the application will create a new one (though you'll lose your data).

4. **Application crashes**: Check the console output for error messages that might indicate database issues.
