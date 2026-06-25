"""
Simple application for the Smart Traffic Analysis System.
This application uses a local SQLite database for storage.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from simple_db import SimpleDatabase

class SimpleTrafficApp:
    """A simple traffic analysis application with local database storage."""
    
    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("Simple Traffic Analysis System")
        self.root.geometry("800x600")
        
        # Connect to the database
        self.db = SimpleDatabase("traffic_local.db")
        
        # Update window title with database info
        db_path = os.path.abspath(self.db.db_file)
        self.root.title(f"Simple Traffic Analysis System - Database: {db_path}")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Database info section
        db_frame = ttk.LabelFrame(main_frame, text="Database Information", padding=10)
        db_frame.pack(fill="x", expand=False, pady=10)
        
        ttk.Label(db_frame, text=f"Database File: {db_path}").pack(anchor="w")
        ttk.Label(db_frame, text="Status: Connected" if self.db.connection else "Status: Disconnected").pack(anchor="w")
        
        # Create tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=10)
        
        # Create tab frames
        self.vehicle_tab = ttk.Frame(self.notebook, padding=10)
        self.violation_tab = ttk.Frame(self.notebook, padding=10)
        self.search_tab = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.vehicle_tab, text="Add Vehicle")
        self.notebook.add(self.violation_tab, text="Add Violation")
        self.notebook.add(self.search_tab, text="Search Records")
        
        # Create vehicle form
        self.create_vehicle_form()
        
        # Create violation form
        self.create_violation_form()
        
        # Create search form
        self.create_search_form()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load initial data
        self.load_initial_data()
    
    def create_vehicle_form(self):
        """Create the vehicle entry form."""
        # Vehicle form
        form_frame = ttk.LabelFrame(self.vehicle_tab, text="Vehicle Information", padding=10)
        form_frame.pack(fill="both", expand=True)
        
        # Plate number
        ttk.Label(form_frame, text="Plate Number:").grid(row=0, column=0, sticky="w", pady=5)
        self.plate_entry = ttk.Entry(form_frame, width=30)
        self.plate_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # Color
        ttk.Label(form_frame, text="Color:").grid(row=1, column=0, sticky="w", pady=5)
        self.color_entry = ttk.Entry(form_frame, width=30)
        self.color_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Speed
        ttk.Label(form_frame, text="Speed (km/h):").grid(row=2, column=0, sticky="w", pady=5)
        self.speed_entry = ttk.Entry(form_frame, width=30)
        self.speed_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        
        # Vehicle type
        ttk.Label(form_frame, text="Vehicle Type:").grid(row=3, column=0, sticky="w", pady=5)
        self.type_entry = ttk.Combobox(form_frame, values=["Car", "Truck", "Motorcycle", "Bus", "Unknown"], width=27)
        self.type_entry.current(0)  # Default to "Car"
        self.type_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        # Submit button
        submit_button = ttk.Button(form_frame, text="Add Vehicle", command=self.add_vehicle)
        submit_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Vehicle count
        self.vehicle_count_var = tk.StringVar(value="Total Vehicles: 0")
        ttk.Label(form_frame, textvariable=self.vehicle_count_var).grid(row=5, column=0, columnspan=2, pady=5)
    
    def create_violation_form(self):
        """Create the violation entry form."""
        # Violation form
        form_frame = ttk.LabelFrame(self.violation_tab, text="Violation Information", padding=10)
        form_frame.pack(fill="both", expand=True)
        
        # Plate number
        ttk.Label(form_frame, text="Plate Number:").grid(row=0, column=0, sticky="w", pady=5)
        self.violation_plate_entry = ttk.Entry(form_frame, width=30)
        self.violation_plate_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # Violation type
        ttk.Label(form_frame, text="Violation Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.violation_type_entry = ttk.Combobox(form_frame, values=["Speeding", "Red Light", "Wrong Lane", "No Seatbelt", "Using Phone"], width=27)
        self.violation_type_entry.current(0)  # Default to "Speeding"
        self.violation_type_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Speed
        ttk.Label(form_frame, text="Speed (km/h):").grid(row=2, column=0, sticky="w", pady=5)
        self.violation_speed_entry = ttk.Entry(form_frame, width=30)
        self.violation_speed_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        
        # Fine amount
        ttk.Label(form_frame, text="Fine Amount:").grid(row=3, column=0, sticky="w", pady=5)
        self.fine_entry = ttk.Entry(form_frame, width=30)
        self.fine_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        # Submit button
        submit_button = ttk.Button(form_frame, text="Add Violation", command=self.add_violation)
        submit_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Violation count
        self.violation_count_var = tk.StringVar(value="Total Violations: 0")
        ttk.Label(form_frame, textvariable=self.violation_count_var).grid(row=5, column=0, columnspan=2, pady=5)
    
    def create_search_form(self):
        """Create the search form."""
        # Search form
        form_frame = ttk.LabelFrame(self.search_tab, text="Search Records", padding=10)
        form_frame.pack(fill="both", expand=True)
        
        # Search options
        search_frame = ttk.Frame(form_frame)
        search_frame.pack(fill="x", expand=False, pady=5)
        
        # Plate number
        ttk.Label(search_frame, text="Plate Number:").grid(row=0, column=0, sticky="w", pady=5)
        self.search_plate_entry = ttk.Entry(search_frame, width=30)
        self.search_plate_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search", command=self.search_records)
        search_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Clear button
        clear_button = ttk.Button(search_frame, text="Clear", command=self.clear_search)
        clear_button.grid(row=0, column=3, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(form_frame, text="Results", padding=10)
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Create treeview for results
        columns = ("ID", "Plate", "Color", "Speed", "Type", "Timestamp")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Configure columns
        self.results_tree.heading("ID", text="ID")
        self.results_tree.heading("Plate", text="Plate Number")
        self.results_tree.heading("Color", text="Color")
        self.results_tree.heading("Speed", text="Speed (km/h)")
        self.results_tree.heading("Type", text="Vehicle Type")
        self.results_tree.heading("Timestamp", text="Timestamp")
        
        # Set column widths
        self.results_tree.column("ID", width=50)
        self.results_tree.column("Plate", width=100)
        self.results_tree.column("Color", width=80)
        self.results_tree.column("Speed", width=80)
        self.results_tree.column("Type", width=100)
        self.results_tree.column("Timestamp", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind double-click event
        self.results_tree.bind("<Double-1>", self.show_vehicle_details)
    
    def load_initial_data(self):
        """Load initial data from the database."""
        try:
            # Get vehicle count
            vehicles = self.db.get_all_vehicles()
            self.vehicle_count_var.set(f"Total Vehicles: {len(vehicles)}")
            
            # Get violation count
            violations = self.db.get_violations()
            self.violation_count_var.set(f"Total Violations: {len(violations)}")
            
            # Update status
            self.status_var.set(f"Connected to database: {self.db.db_file}")
        except Exception as e:
            self.status_var.set(f"Error loading data: {str(e)}")
    
    def add_vehicle(self):
        """Add a vehicle to the database."""
        try:
            # Get form data
            plate = self.plate_entry.get().strip()
            color = self.color_entry.get().strip()
            speed_str = self.speed_entry.get().strip()
            vehicle_type = self.type_entry.get()
            
            # Validate input
            if not plate:
                messagebox.showerror("Error", "Plate number is required")
                return
            
            if not color:
                messagebox.showerror("Error", "Color is required")
                return
            
            try:
                speed = int(speed_str)
                if speed <= 0:
                    messagebox.showerror("Error", "Speed must be a positive number")
                    return
            except ValueError:
                messagebox.showerror("Error", "Speed must be a number")
                return
            
            # Add vehicle to database
            result = self.db.add_vehicle(plate, color, speed, vehicle_type)
            
            if result:
                # Clear form
                self.plate_entry.delete(0, tk.END)
                self.color_entry.delete(0, tk.END)
                self.speed_entry.delete(0, tk.END)
                
                # Update vehicle count
                vehicles = self.db.get_all_vehicles()
                self.vehicle_count_var.set(f"Total Vehicles: {len(vehicles)}")
                
                # Show success message
                messagebox.showinfo("Success", f"Vehicle {plate} added successfully")
                
                # Update status
                self.status_var.set(f"Vehicle {plate} added successfully")
            else:
                messagebox.showerror("Error", "Failed to add vehicle")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def add_violation(self):
        """Add a violation to the database."""
        try:
            # Get form data
            plate = self.violation_plate_entry.get().strip()
            violation_type = self.violation_type_entry.get()
            speed_str = self.violation_speed_entry.get().strip()
            fine_str = self.fine_entry.get().strip()
            
            # Validate input
            if not plate:
                messagebox.showerror("Error", "Plate number is required")
                return
            
            try:
                speed = int(speed_str)
                if speed <= 0:
                    messagebox.showerror("Error", "Speed must be a positive number")
                    return
            except ValueError:
                messagebox.showerror("Error", "Speed must be a number")
                return
            
            try:
                fine = float(fine_str)
                if fine <= 0:
                    messagebox.showerror("Error", "Fine amount must be a positive number")
                    return
            except ValueError:
                messagebox.showerror("Error", "Fine amount must be a number")
                return
            
            # Add violation to database
            result = self.db.add_violation(plate, violation_type, speed, fine)
            
            if result:
                # Clear form
                self.violation_plate_entry.delete(0, tk.END)
                self.violation_speed_entry.delete(0, tk.END)
                self.fine_entry.delete(0, tk.END)
                
                # Update violation count
                violations = self.db.get_violations()
                self.violation_count_var.set(f"Total Violations: {len(violations)}")
                
                # Show success message
                messagebox.showinfo("Success", f"Violation for {plate} added successfully")
                
                # Update status
                self.status_var.set(f"Violation for {plate} added successfully")
            else:
                messagebox.showerror("Error", "Failed to add violation")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def search_records(self):
        """Search for vehicles in the database."""
        try:
            # Get search criteria
            plate = self.search_plate_entry.get().strip()
            
            # Clear results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Get vehicles
            if plate:
                # Get specific vehicle
                vehicle = self.db.get_vehicle_info(plate)
                if vehicle:
                    self.results_tree.insert("", "end", values=(
                        vehicle[0],  # ID
                        vehicle[1],  # Plate
                        vehicle[2],  # Color
                        vehicle[3],  # Speed
                        vehicle[4],  # Type
                        vehicle[5]   # Timestamp
                    ))
            else:
                # Get all vehicles
                vehicles = self.db.get_all_vehicles()
                for vehicle in vehicles:
                    self.results_tree.insert("", "end", values=(
                        vehicle[0],  # ID
                        vehicle[1],  # Plate
                        vehicle[2],  # Color
                        vehicle[3],  # Speed
                        vehicle[4],  # Type
                        vehicle[5]   # Timestamp
                    ))
            
            # Update status
            count = len(self.results_tree.get_children())
            self.status_var.set(f"Found {count} vehicles")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def clear_search(self):
        """Clear the search form and results."""
        self.search_plate_entry.delete(0, tk.END)
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Update status
        self.status_var.set("Search cleared")
    
    def show_vehicle_details(self, event):
        """Show vehicle details when a row is double-clicked."""
        # Get selected item
        item = self.results_tree.selection()[0]
        values = self.results_tree.item(item, "values")
        
        # Get vehicle ID
        vehicle_id = values[0]
        plate = values[1]
        
        # Get violations for this vehicle
        violations = self.db.get_violations(plate)
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Vehicle Details: {plate}")
        details_window.geometry("600x400")
        
        # Vehicle details
        details_frame = ttk.LabelFrame(details_window, text="Vehicle Information", padding=10)
        details_frame.pack(fill="x", expand=False, padx=10, pady=10)
        
        ttk.Label(details_frame, text=f"ID: {values[0]}").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(details_frame, text=f"Plate: {values[1]}").grid(row=0, column=1, sticky="w", pady=2)
        ttk.Label(details_frame, text=f"Color: {values[2]}").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(details_frame, text=f"Speed: {values[3]} km/h").grid(row=1, column=1, sticky="w", pady=2)
        ttk.Label(details_frame, text=f"Type: {values[4]}").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(details_frame, text=f"Timestamp: {values[5]}").grid(row=2, column=1, sticky="w", pady=2)
        
        # Violations
        violations_frame = ttk.LabelFrame(details_window, text="Violations", padding=10)
        violations_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        if violations:
            # Create treeview for violations
            columns = ("ID", "Type", "Speed", "Fine", "Status", "Timestamp")
            violations_tree = ttk.Treeview(violations_frame, columns=columns, show="headings")
            
            # Configure columns
            violations_tree.heading("ID", text="ID")
            violations_tree.heading("Type", text="Violation Type")
            violations_tree.heading("Speed", text="Speed (km/h)")
            violations_tree.heading("Fine", text="Fine Amount")
            violations_tree.heading("Status", text="Status")
            violations_tree.heading("Timestamp", text="Timestamp")
            
            # Set column widths
            violations_tree.column("ID", width=50)
            violations_tree.column("Type", width=100)
            violations_tree.column("Speed", width=80)
            violations_tree.column("Fine", width=80)
            violations_tree.column("Status", width=80)
            violations_tree.column("Timestamp", width=150)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(violations_frame, orient="vertical", command=violations_tree.yview)
            violations_tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack treeview and scrollbar
            violations_tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add violations to treeview
            for violation in violations:
                violations_tree.insert("", "end", values=(
                    violation[0],  # ID
                    violation[2],  # Type
                    violation[3],  # Speed
                    violation[4],  # Fine
                    violation[5],  # Status
                    violation[6]   # Timestamp
                ))
        else:
            ttk.Label(violations_frame, text="No violations found for this vehicle").pack(pady=20)
        
        # Close button
        ttk.Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)

def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = SimpleTrafficApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
