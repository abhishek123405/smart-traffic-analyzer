"""
Main application for the Smart Traffic Analysis System using local storage.
This version uses a simple SQLite database for local storage.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from gui import TrafficGUI
from simple_db import SimpleDatabase

def main():
    """Main function to run the application."""
    # Create the main window
    root = tk.Tk()
    root.title("Smart Traffic Analysis System - Local Storage")
    root.geometry("800x600")
    
    # Create a frame to show database information
    info_frame = ttk.Frame(root, padding=10)
    info_frame.pack(fill="x", expand=False)
    
    # Create the database
    db = SimpleDatabase("traffic_local.db")
    
    # Show database information
    db_path = os.path.abspath(db.db_file)
    ttk.Label(info_frame, text=f"Database: {db_path}", font=("Arial", 10, "bold")).pack(anchor="w")
    ttk.Label(info_frame, text="Status: Connected", foreground="green").pack(anchor="w")
    
    # Create the main application
    app = TrafficGUI(root, db)
    
    # Start the main loop
    root.mainloop()
    
    # Close the database connection
    db.close()

if __name__ == "__main__":
    main()
