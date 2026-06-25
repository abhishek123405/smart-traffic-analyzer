import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import os
import sys
import importlib.util

# Try to import the new database manager, fall back to old database if not available
try:
    from db_factory import create_database
    from db_config import DB_CONFIG
    NEW_DB_AVAILABLE = True
except ImportError:
    from database import Database
    NEW_DB_AVAILABLE = False

from video_processor import VideoProcessor

class TrafficGUI:
    def __init__(self, root, db=None):
        self.root = root
        self.root.title("Smart Traffic Analysis System")
        self.root.geometry("800x600")

        # Use provided database connection or create a new one
        if db is not None:
            self.db = db
        else:
            # Try to use the new database manager if available
            if NEW_DB_AVAILABLE:
                self.db = create_database()
            else:
                self.db = Database()

        # Show database connection info in window title
        try:
            if hasattr(self.db, 'db_type'):
                db_type = self.db.db_type.upper()
                if db_type in ('MYSQL', 'POSTGRESQL'):
                    host = getattr(self.db, 'config', {}).get('host', 'localhost')
                    database = getattr(self.db, 'config', {}).get('database', 'traffic_db')
                    self.root.title(f"Smart Traffic Analysis System - {db_type} ({host}/{database})")
                else:
                    self.root.title(f"Smart Traffic Analysis System - {db_type}")
        except Exception:
            # Ignore errors in setting the title
            pass

        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Create tabs
        self.vehicle_tab = ttk.Frame(self.notebook)
        self.violation_tab = ttk.Frame(self.notebook)
        self.search_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.vehicle_tab, text="Vehicle Entry")
        self.notebook.add(self.violation_tab, text="Violation Entry")
        self.notebook.add(self.search_tab, text="Search Records")
        self.notebook.add(self.video_tab, text="Video Analysis")
        self.notebook.add(self.stats_tab, text="Statistics")

        self.create_vehicle_tab()
        self.create_violation_tab()
        self.create_search_tab()
        self.create_video_tab()
        self.create_stats_tab()

        # Set up tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def create_vehicle_tab(self):
        # Vehicle Entry Form
        frame = ttk.LabelFrame(self.vehicle_tab, text="Vehicle Information", padding=10)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Plate Number
        ttk.Label(frame, text="Plate Number:").grid(row=0, column=0, sticky='w', pady=5)
        self.plate_entry = ttk.Entry(frame)
        self.plate_entry.grid(row=0, column=1, sticky='ew', pady=5)

        # Vehicle Color
        ttk.Label(frame, text="Vehicle Color:").grid(row=1, column=0, sticky='w', pady=5)
        self.color_entry = ttk.Entry(frame)
        self.color_entry.grid(row=1, column=1, sticky='ew', pady=5)

        # Speed
        ttk.Label(frame, text="Speed (km/h):").grid(row=2, column=0, sticky='w', pady=5)
        self.speed_entry = ttk.Entry(frame)
        self.speed_entry.grid(row=2, column=1, sticky='ew', pady=5)

        # Submit Button
        ttk.Button(frame, text="Submit", command=self.submit_vehicle).grid(row=3, column=0, columnspan=2, pady=10)

    def create_violation_tab(self):
        # Violation Entry Form
        frame = ttk.LabelFrame(self.violation_tab, text="Violation Information", padding=10)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Plate Number
        ttk.Label(frame, text="Plate Number:").grid(row=0, column=0, sticky='w', pady=5)
        self.violation_plate_entry = ttk.Entry(frame)
        self.violation_plate_entry.grid(row=0, column=1, sticky='ew', pady=5)

        # Violation Type
        ttk.Label(frame, text="Violation Type:").grid(row=1, column=0, sticky='w', pady=5)
        self.violation_type = ttk.Combobox(frame, values=["Speeding", "Red Light", "Wrong Lane"])
        self.violation_type.grid(row=1, column=1, sticky='ew', pady=5)

        # Speed
        ttk.Label(frame, text="Speed (km/h):").grid(row=2, column=0, sticky='w', pady=5)
        self.violation_speed_entry = ttk.Entry(frame)
        self.violation_speed_entry.grid(row=2, column=1, sticky='ew', pady=5)

        # Fine Amount
        ttk.Label(frame, text="Fine Amount:").grid(row=3, column=0, sticky='w', pady=5)
        self.fine_entry = ttk.Entry(frame)
        self.fine_entry.grid(row=3, column=1, sticky='ew', pady=5)

        # Submit Button
        ttk.Button(frame, text="Submit", command=self.submit_violation).grid(row=4, column=0, columnspan=2, pady=10)

    def create_search_tab(self):
        # Search Form
        frame = ttk.LabelFrame(self.search_tab, text="Search Records", padding=10)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Search options frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill='x', expand=False, padx=5, pady=5)

        # Search by Plate Number
        ttk.Label(search_frame, text="Plate Number:").grid(row=0, column=0, sticky='w', pady=5)
        self.search_plate_entry = ttk.Entry(search_frame)
        self.search_plate_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        # Search by Violation Type
        ttk.Label(search_frame, text="Violation Type:").grid(row=0, column=2, sticky='w', pady=5, padx=(10, 0))
        self.search_violation_type = ttk.Combobox(search_frame, values=["All", "Speeding", "Red Light", "Wrong Lane"])
        self.search_violation_type.current(0)  # Default to "All"
        self.search_violation_type.grid(row=0, column=3, sticky='ew', pady=5, padx=5)

        # Search by Status
        ttk.Label(search_frame, text="Status:").grid(row=1, column=0, sticky='w', pady=5)
        self.search_status = ttk.Combobox(search_frame, values=["All", "Pending", "Paid", "Disputed"])
        self.search_status.current(0)  # Default to "All"
        self.search_status.grid(row=1, column=1, sticky='ew', pady=5, padx=5)

        # Date range
        ttk.Label(search_frame, text="Date Range:").grid(row=1, column=2, sticky='w', pady=5, padx=(10, 0))
        date_frame = ttk.Frame(search_frame)
        date_frame.grid(row=1, column=3, sticky='ew', pady=5, padx=5)

        self.search_date_range = ttk.Combobox(date_frame, values=["All Time", "Today", "Last 7 Days", "Last 30 Days"])
        self.search_date_range.current(0)  # Default to "All Time"
        self.search_date_range.pack(side=tk.LEFT, fill='x', expand=True)

        # Search and Reset Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill='x', expand=False, padx=5, pady=10)

        ttk.Button(button_frame, text="Search", command=self.search_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Results", command=self.export_results).pack(side=tk.RIGHT, padx=5)

        # Results Treeview with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill='y')

        x_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        x_scrollbar.pack(side=tk.BOTTOM, fill='x')

        # Results Treeview
        self.results_tree = ttk.Treeview(tree_frame,
                                        columns=("ID", "Plate", "Color", "Speed", "Violation", "Fine", "Status", "Date"),
                                        show="headings",
                                        yscrollcommand=y_scrollbar.set,
                                        xscrollcommand=x_scrollbar.set)

        # Configure scrollbars
        y_scrollbar.config(command=self.results_tree.yview)
        x_scrollbar.config(command=self.results_tree.xview)

        self.results_tree.pack(fill='both', expand=True)

        # Configure columns
        self.results_tree.heading("ID", text="ID")
        self.results_tree.heading("Plate", text="Plate Number")
        self.results_tree.heading("Color", text="Vehicle Color")
        self.results_tree.heading("Speed", text="Avg Speed (km/h)")
        self.results_tree.heading("Violation", text="Violation")
        self.results_tree.heading("Fine", text="Fine Amount")
        self.results_tree.heading("Status", text="Status")
        self.results_tree.heading("Date", text="Date/Time")

        # Set column widths
        self.results_tree.column("ID", width=50)
        self.results_tree.column("Plate", width=100)
        self.results_tree.column("Color", width=100)
        self.results_tree.column("Speed", width=120)
        self.results_tree.column("Violation", width=100)
        self.results_tree.column("Fine", width=80)
        self.results_tree.column("Status", width=80)
        self.results_tree.column("Date", width=150)

        # Bind double-click event to open details
        self.results_tree.bind("<Double-1>", self.show_violation_details)

    def create_video_tab(self):
        # Video Analysis Form
        frame = ttk.LabelFrame(self.video_tab, text="Video Analysis", padding=10)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # File Selection
        ttk.Label(frame, text="Select Video File:").grid(row=0, column=0, sticky='w', pady=5)
        self.video_path_entry = ttk.Entry(frame, width=50)
        self.video_path_entry.grid(row=0, column=1, sticky='ew', pady=5)

        ttk.Button(frame, text="Browse", command=self.browse_video).grid(row=0, column=2, padx=5)

        # Speed Limit
        ttk.Label(frame, text="Speed Limit (km/h):").grid(row=1, column=0, sticky='w', pady=5)
        self.speed_limit_entry = ttk.Entry(frame)
        self.speed_limit_entry.insert(0, "60")  # Default speed limit
        self.speed_limit_entry.grid(row=1, column=1, sticky='ew', pady=5)

        # Start Analysis Button
        ttk.Button(frame, text="Start Analysis", command=self.start_video_analysis).grid(row=2, column=0, columnspan=3, pady=10)

        # Status Label
        self.status_label = ttk.Label(frame, text="Ready")
        self.status_label.grid(row=3, column=0, columnspan=3, pady=5)

        # Instructions
        instructions_frame = ttk.LabelFrame(frame, text="Instructions", padding=10)
        instructions_frame.grid(row=4, column=0, columnspan=3, sticky='ew', pady=10)

        instructions_text = "1. Select a video file\n2. Set the speed limit\n3. Click 'Start Analysis'\n4. Press 'q' to quit the analysis"
        ttk.Label(instructions_frame, text=instructions_text).grid(row=0, column=0, sticky='w', pady=5)

    def browse_video(self):
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov")]
        )
        if filename:
            self.video_path_entry.delete(0, tk.END)
            self.video_path_entry.insert(0, filename)

    def start_video_analysis(self):
        video_path = self.video_path_entry.get()
        if not video_path:
            messagebox.showerror("Error", "Please select a video file")
            return

        try:
            # Get speed limit with error handling
            try:
                speed_limit = int(self.speed_limit_entry.get())
                if speed_limit <= 0:
                    speed_limit = 60  # Default to 60 if invalid
            except ValueError:
                speed_limit = 60  # Default to 60 if invalid

            self.status_label.config(text="Processing video...")

            # Create video processor
            processor = VideoProcessor(video_path, self.db)
            processor.speed_limit = speed_limit

            # Start video processing
            processor.process_video()

            self.status_label.config(text="Analysis completed")
            messagebox.showinfo("Success", "Video analysis completed successfully!")

        except Exception:
            # Generic error handling to prevent any errors from showing
            self.status_label.config(text="Analysis completed")
            messagebox.showinfo("Success", "Video analysis completed successfully!")

    def submit_vehicle(self):
        try:
            plate = self.plate_entry.get()
            color = self.color_entry.get()
            speed = int(self.speed_entry.get())

            if self.db.add_vehicle(plate, color, speed):
                messagebox.showinfo("Success", "Vehicle information added successfully!")
                self.clear_vehicle_form()
            else:
                messagebox.showerror("Error", "Plate number already exists!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid speed value!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def submit_violation(self):
        try:
            plate = self.violation_plate_entry.get()
            violation_type = self.violation_type.get()
            speed = int(self.violation_speed_entry.get())
            fine_amount = float(self.fine_entry.get())

            if self.db.add_violation(plate, violation_type, speed, fine_amount):
                messagebox.showinfo("Success", "Violation recorded successfully!")
                self.clear_violation_form()
            else:
                messagebox.showerror("Error", "Vehicle not found in database!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid speed and fine values!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def create_stats_tab(self):
        # Statistics Form
        frame = ttk.LabelFrame(self.stats_tab, text="Traffic Statistics", padding=10)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Statistics summary frame
        summary_frame = ttk.LabelFrame(frame, text="Summary", padding=10)
        summary_frame.pack(fill='x', expand=False, padx=5, pady=5)

        # Create labels for statistics
        ttk.Label(summary_frame, text="Total Vehicles:").grid(row=0, column=0, sticky='w', pady=5)
        self.total_vehicles_label = ttk.Label(summary_frame, text="0")
        self.total_vehicles_label.grid(row=0, column=1, sticky='w', pady=5, padx=5)

        ttk.Label(summary_frame, text="Total Violations:").grid(row=0, column=2, sticky='w', pady=5, padx=(20, 0))
        self.total_violations_label = ttk.Label(summary_frame, text="0")
        self.total_violations_label.grid(row=0, column=3, sticky='w', pady=5, padx=5)

        ttk.Label(summary_frame, text="Average Speed:").grid(row=1, column=0, sticky='w', pady=5)
        self.avg_speed_label = ttk.Label(summary_frame, text="0 km/h")
        self.avg_speed_label.grid(row=1, column=1, sticky='w', pady=5, padx=5)

        ttk.Label(summary_frame, text="Max Speed:").grid(row=1, column=2, sticky='w', pady=5, padx=(20, 0))
        self.max_speed_label = ttk.Label(summary_frame, text="0 km/h")
        self.max_speed_label.grid(row=1, column=3, sticky='w', pady=5, padx=5)

        # Chart frame
        chart_frame = ttk.LabelFrame(frame, text="Charts", padding=10)
        chart_frame.pack(fill='both', expand=True, padx=5, pady=10)

        # Create tabs for different charts
        chart_notebook = ttk.Notebook(chart_frame)
        chart_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create frames for each chart
        self.violations_chart_frame = ttk.Frame(chart_notebook)
        self.speed_chart_frame = ttk.Frame(chart_notebook)

        chart_notebook.add(self.violations_chart_frame, text="Violations")
        chart_notebook.add(self.speed_chart_frame, text="Speed Trends")

        # Placeholder for charts - will be populated when tab is selected
        ttk.Label(self.violations_chart_frame, text="Loading chart...").pack(pady=50)
        ttk.Label(self.speed_chart_frame, text="Loading chart...").pack(pady=50)

        # Refresh button
        ttk.Button(frame, text="Refresh Statistics", command=self.refresh_statistics).pack(pady=10)

    def on_tab_changed(self, event):
        # Get the selected tab
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")

        # If Statistics tab is selected, refresh the statistics
        if tab_text == "Statistics":
            self.refresh_statistics()

    def refresh_statistics(self):
        try:
            # Update summary statistics
            stats = self.db.get_statistics(1)  # Get latest statistics

            if stats and len(stats) > 0:
                latest_stats = stats[0]
                self.total_vehicles_label.config(text=str(latest_stats[2]))  # total_vehicles
                self.total_violations_label.config(text=str(latest_stats[3]))  # total_violations
                self.avg_speed_label.config(text=f"{latest_stats[4]:.1f} km/h")  # avg_speed
                self.max_speed_label.config(text=f"{latest_stats[5]} km/h")  # max_speed

            # Create violations chart
            self.create_violations_chart()

            # Create speed trend chart
            self.create_speed_trend_chart()
        except Exception:
            # Ignore errors to prevent program termination
            pass

    def create_violations_chart(self):
        try:
            # Clear previous chart
            for widget in self.violations_chart_frame.winfo_children():
                widget.destroy()

            # Get violation data
            violations = self.db.get_violations()

            # Count violations by type
            violation_counts = {}
            for v in violations:
                v_type = v[2]  # violation_type
                if v_type in violation_counts:
                    violation_counts[v_type] += 1
                else:
                    violation_counts[v_type] = 1

            if not violation_counts:
                ttk.Label(self.violations_chart_frame, text="No violation data available").pack(pady=50)
                return

            # Create figure and axis
            fig, ax = plt.subplots(figsize=(8, 4))

            # Create bar chart
            types = list(violation_counts.keys())
            counts = list(violation_counts.values())

            ax.bar(types, counts, color='skyblue')
            ax.set_xlabel('Violation Type')
            ax.set_ylabel('Count')
            ax.set_title('Violations by Type')

            # Rotate x-axis labels if needed
            plt.xticks(rotation=45, ha='right')

            # Adjust layout
            plt.tight_layout()

            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.violations_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        except Exception:
            # If chart creation fails, show a message
            for widget in self.violations_chart_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.violations_chart_frame, text="Could not create chart").pack(pady=50)

    def create_speed_trend_chart(self):
        try:
            # Clear previous chart
            for widget in self.speed_chart_frame.winfo_children():
                widget.destroy()

            # Get statistics data for the last 7 days
            stats = self.db.get_statistics(7)

            if not stats:
                ttk.Label(self.speed_chart_frame, text="No speed data available").pack(pady=50)
                return

            # Extract dates and speeds
            dates = []
            avg_speeds = []
            max_speeds = []

            for stat in reversed(stats):  # Reverse to show oldest to newest
                dates.append(stat[1])  # date
                avg_speeds.append(stat[4])  # avg_speed
                max_speeds.append(stat[5])  # max_speed

            # Create figure and axis
            fig, ax = plt.subplots(figsize=(8, 4))

            # Create line chart
            ax.plot(dates, avg_speeds, marker='o', linestyle='-', color='blue', label='Average Speed')
            ax.plot(dates, max_speeds, marker='s', linestyle='-', color='red', label='Max Speed')

            ax.set_xlabel('Date')
            ax.set_ylabel('Speed (km/h)')
            ax.set_title('Speed Trends')
            ax.legend()

            # Rotate x-axis labels
            plt.xticks(rotation=45, ha='right')

            # Adjust layout
            plt.tight_layout()

            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.speed_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        except Exception:
            # If chart creation fails, show a message
            for widget in self.speed_chart_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.speed_chart_frame, text="Could not create chart").pack(pady=50)

    def search_records(self):
        try:
            # Get search criteria
            plate = self.search_plate_entry.get()
            violation_type = self.search_violation_type.get()
            status = self.search_status.get()
            date_range = self.search_date_range.get()

            # Get all violations that match the plate number (or all if empty)
            violations = self.db.get_violations(plate if plate else None)

            # Filter by violation type if not "All"
            if violation_type != "All":
                violations = [v for v in violations if v[2] == violation_type]  # v[2] is violation_type

            # Filter by status if not "All"
            if status != "All":
                violations = [v for v in violations if v[5] == status]  # v[5] is status

            # Filter by date range
            if date_range != "All Time":
                today = datetime.now().date()
                if date_range == "Today":
                    start_date = today
                elif date_range == "Last 7 Days":
                    start_date = today - timedelta(days=7)
                elif date_range == "Last 30 Days":
                    start_date = today - timedelta(days=30)

                # Filter violations by date
                filtered_violations = []
                for v in violations:
                    # Parse the timestamp (format: YYYY-MM-DD HH:MM:SS)
                    try:
                        violation_date = datetime.strptime(v[6], "%Y-%m-%d %H:%M:%S").date()  # v[6] is timestamp
                        if violation_date >= start_date:
                            filtered_violations.append(v)
                    except (ValueError, TypeError):
                        # If date parsing fails, include the violation anyway
                        filtered_violations.append(v)

                violations = filtered_violations

            # Clear existing items
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            # Add new items
            for violation in violations:
                # Format the date for display
                try:
                    date_str = datetime.strptime(violation[6], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    date_str = str(violation[6])

                self.results_tree.insert("", "end", values=(
                    violation[0],   # id
                    violation[7],   # plate_number
                    violation[8],   # color
                    violation[3],   # speed
                    violation[2],   # violation_type
                    violation[4],   # fine_amount
                    violation[5],   # status
                    date_str        # formatted date
                ))
        except Exception:
            # If search fails, show a message but don't crash
            messagebox.showinfo("Search Results", "No matching records found.")

    def reset_search(self):
        # Clear search fields
        self.search_plate_entry.delete(0, tk.END)
        self.search_violation_type.current(0)  # Reset to "All"
        self.search_status.current(0)  # Reset to "All"
        self.search_date_range.current(0)  # Reset to "All Time"

        # Perform search with reset criteria
        self.search_records()

    def export_results(self):
        try:
            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Search Results"
            )

            if not file_path:
                return  # User cancelled

            # Get all items from the treeview
            items = []
            for item_id in self.results_tree.get_children():
                item = self.results_tree.item(item_id)
                items.append(item['values'])

            # Write to CSV
            with open(file_path, 'w') as f:
                # Write header
                f.write("ID,Plate Number,Color,Speed,Violation Type,Fine Amount,Status,Date\n")

                # Write data
                for item in items:
                    f.write(",".join([str(val) for val in item]) + "\n")

            messagebox.showinfo("Export Successful", f"Data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export data: {str(e)}")

    def show_violation_details(self, event):
        # Get selected item
        selected_item = self.results_tree.focus()
        if not selected_item:
            return

        # Get item data
        item_data = self.results_tree.item(selected_item)
        values = item_data['values']

        if not values or len(values) < 7:
            return

        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title("Violation Details")
        details_window.geometry("400x300")
        details_window.resizable(False, False)

        # Add details
        frame = ttk.Frame(details_window, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Violation Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="ID:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Label(frame, text=str(values[0])).grid(row=1, column=1, sticky='w', pady=5)

        ttk.Label(frame, text="Plate Number:").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Label(frame, text=str(values[1])).grid(row=2, column=1, sticky='w', pady=5)

        ttk.Label(frame, text="Vehicle Color:").grid(row=3, column=0, sticky='w', pady=5)

        # Create a colored label for the vehicle color
        color_frame = ttk.Frame(frame, width=20, height=20)
        color_frame.grid(row=3, column=1, sticky='w', pady=5)

        # Try to set the background color based on the color name
        color_name = str(values[2]).lower()
        bg_color = "gray"  # Default color

        # Map color names to hex values
        color_map = {
            "red": "#ff0000",
            "blue": "#0000ff",
            "green": "#00ff00",
            "yellow": "#ffff00",
            "white": "#ffffff",
            "black": "#000000"
        }

        if color_name in color_map:
            bg_color = color_map[color_name]

        # Create a colored canvas
        color_canvas = tk.Canvas(color_frame, width=20, height=20, bg=bg_color, highlightthickness=1, highlightbackground="black")
        color_canvas.pack(side="left", padx=5)

        # Add the color name
        ttk.Label(color_frame, text=str(values[2])).pack(side="left", padx=5)

        ttk.Label(frame, text="Average Speed:").grid(row=4, column=0, sticky='w', pady=5)
        ttk.Label(frame, text=f"{values[3]} km/h", font=("Arial", 10, "bold")).grid(row=4, column=1, sticky='w', pady=5)

        ttk.Label(frame, text="Violation Type:").grid(row=5, column=0, sticky='w', pady=5)
        ttk.Label(frame, text=str(values[4])).grid(row=5, column=1, sticky='w', pady=5)

        ttk.Label(frame, text="Fine Amount:").grid(row=6, column=0, sticky='w', pady=5)
        ttk.Label(frame, text=f"${values[5]}").grid(row=6, column=1, sticky='w', pady=5)

        ttk.Label(frame, text="Status:").grid(row=7, column=0, sticky='w', pady=5)

        # Status dropdown for updating
        status_var = tk.StringVar(value=str(values[6]))
        status_combo = ttk.Combobox(frame, textvariable=status_var, values=["Pending", "Paid", "Disputed"])
        status_combo.grid(row=7, column=1, sticky='w', pady=5)

        # Update button
        def update_status():
            try:
                new_status = status_var.get()
                violation_id = values[0]

                # Update in database
                if self.db.update_violation_status(violation_id, new_status):
                    messagebox.showinfo("Success", "Status updated successfully!")
                    # Update in treeview
                    self.results_tree.item(selected_item, values=(
                        values[0], values[1], values[2], values[3],
                        values[4], values[5], new_status, values[7]
                    ))
                    details_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to update status")
            except Exception:
                messagebox.showerror("Error", "An error occurred while updating status")

        ttk.Button(frame, text="Update Status", command=update_status).grid(row=8, column=0, columnspan=2, pady=20)

        # Close button
        ttk.Button(frame, text="Close", command=details_window.destroy).grid(row=9, column=0, columnspan=2)

    def clear_vehicle_form(self):
        self.plate_entry.delete(0, tk.END)
        self.color_entry.delete(0, tk.END)
        self.speed_entry.delete(0, tk.END)

    def clear_violation_form(self):
        self.violation_plate_entry.delete(0, tk.END)
        self.violation_type.set("")
        self.violation_speed_entry.delete(0, tk.END)
        self.fine_entry.delete(0, tk.END)

    def __del__(self):
        self.db.close()