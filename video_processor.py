import cv2
import numpy as np
from datetime import datetime
import time
import imutils
from collections import OrderedDict

class CentroidTracker:
    def __init__(self, maxDisappeared=30, maxDistance=50):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.maxDisappeared = maxDisappeared
        self.maxDistance = maxDistance

    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1
        return self.nextObjectID - 1

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.disappeared[objectID]

    def update(self, rects):
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)
            return self.objects

        inputCentroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (x, y, w, h)) in enumerate(rects):
            cX = int(x + w / 2.0)
            cY = int(y + h / 2.0)
            inputCentroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i])
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = np.zeros((len(objectCentroids), len(inputCentroids)))
            for i in range(len(objectCentroids)):
                for j in range(len(inputCentroids)):
                    D[i][j] = np.linalg.norm(objectCentroids[i] - inputCentroids[j])

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue
                if D[row][col] > self.maxDistance:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.disappeared[objectID] = 0
                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1
                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col])

        return self.objects

class VideoProcessor:
    def __init__(self, video_path, db):
        self.video_path = video_path
        self.db = db
        self.cap = cv2.VideoCapture(video_path)
        self.frame_count = 0
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        # Initialize background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, detectShadows=False)

        # Initialize centroid tracker
        self.tracker = CentroidTracker(maxDisappeared=30, maxDistance=50)

        # Parameters for vehicle detection
        self.min_area = 500  # Minimum contour area to be considered a vehicle
        self.vehicle_info = {}  # Dictionary to store vehicle information

        # Auto-calibration parameters (default values)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # Default assumption: 10 pixels = 1 meter (can be adjusted based on camera position)
        self.pixels_per_meter = 10.0

        # Speed calculation parameters
        self.speed_limit = 60  # km/h

        # Speed smoothing parameters
        self.speed_history_size = 5  # Number of speed measurements to keep for smoothing
        self.min_tracking_time = 0.5  # Minimum time (seconds) to track before calculating speed
        self.max_speed_threshold = 150  # Maximum realistic speed in km/h
        self.min_speed_threshold = 1  # Minimum realistic speed in km/h

        # Color detection parameters
        self.color_ranges = {
            'red': ([0, 50, 50], [10, 255, 255]),  # Red color range in HSV
            'blue': ([100, 50, 50], [130, 255, 255]),  # Blue color range in HSV
            'green': ([40, 50, 50], [80, 255, 255]),  # Green color range in HSV
            'yellow': ([20, 100, 100], [40, 255, 255]),  # Yellow color range in HSV
            'white': ([0, 0, 200], [180, 30, 255]),  # White color range in HSV
            'black': ([0, 0, 0], [180, 255, 30])  # Black color range in HSV
        }

    def auto_calibrate(self):
        """Automatically set pixels_per_meter based on frame size"""
        # This is a simple heuristic approach - in a real system, you would use camera parameters
        # or known reference objects for more accurate calibration

        # Adjust pixels_per_meter based on frame size
        # Larger frames typically mean more pixels per meter
        if self.frame_width > 1920:  # 4K or higher
            self.pixels_per_meter = 20.0
        elif self.frame_width > 1280:  # 1080p
            self.pixels_per_meter = 15.0
        elif self.frame_width > 640:  # 720p
            self.pixels_per_meter = 10.0
        else:  # SD or lower
            self.pixels_per_meter = 5.0

        return self.pixels_per_meter

    def calculate_speed(self, start_point, end_point, time_diff):
        """Calculate speed in km/h using pixel distance and time"""
        try:
            if time_diff == 0:
                return 0

            # Calculate distance in meters
            pixel_distance = np.linalg.norm(np.array(end_point) - np.array(start_point))
            distance_meters = pixel_distance / self.pixels_per_meter

            # Calculate speed in m/s
            speed_mps = distance_meters / time_diff

            # Convert to km/h
            speed_kmh = speed_mps * 3.6

            # Apply speed validation
            if speed_kmh > self.max_speed_threshold or speed_kmh < self.min_speed_threshold:
                return 0

            return speed_kmh
        except Exception:
            # Return a default speed to avoid errors
            return 0

    def smooth_speed(self, vehicle_id, new_speed):
        """Apply moving average smoothing to speed measurements"""
        # Initialize speed history if it doesn't exist
        if 'speed_history' not in self.vehicle_info[vehicle_id]:
            self.vehicle_info[vehicle_id]['speed_history'] = []

        # Add new speed to history
        speed_history = self.vehicle_info[vehicle_id]['speed_history']
        speed_history.append(new_speed)

        # Keep only the most recent measurements
        if len(speed_history) > self.speed_history_size:
            speed_history = speed_history[-self.speed_history_size:]
            self.vehicle_info[vehicle_id]['speed_history'] = speed_history

        # Calculate smoothed speed (ignore zero values)
        non_zero_speeds = [s for s in speed_history if s > 0]
        if non_zero_speeds:
            avg_speed = sum(non_zero_speeds) / len(non_zero_speeds)
            # Store the average speed
            self.vehicle_info[vehicle_id]['avg_speed'] = avg_speed
            return avg_speed
        return 0

    def detect_color(self, frame, bbox):
        """Detect the dominant color of a vehicle in the given bounding box"""
        try:
            # Extract the region of interest (ROI)
            x, y, w, h = bbox
            roi = frame[y:y+h, x:x+w]

            # Convert ROI to HSV color space
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # Calculate the dominant color
            color_scores = {}
            for color_name, (lower, upper) in self.color_ranges.items():
                # Create a mask for this color range
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                mask = cv2.inRange(hsv_roi, lower, upper)

                # Calculate the percentage of pixels in this color range
                color_scores[color_name] = (cv2.countNonZero(mask) / (w * h)) * 100

            # Get the color with the highest score
            dominant_color = max(color_scores.items(), key=lambda x: x[1])

            # Only return the color if it's above a threshold
            if dominant_color[1] > 10:  # At least 10% of pixels match this color
                return dominant_color[0]
            else:
                return "unknown"
        except Exception as e:
            print(f"Error detecting color: {str(e)}")
            return "unknown"

    def process_frame(self, frame):
        try:
            # Resize frame for faster processing
            frame = imutils.resize(frame, width=800)
        except Exception:
            # If frame processing fails, return an empty frame
            return np.zeros((600, 800, 3), dtype=np.uint8)

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(fg_mask, 25, 255, cv2.THRESH_BINARY)

        # Apply morphological operations to remove noise
        kernel = np.ones((5,5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get bounding rectangles for all valid contours
        rects = []
        for contour in contours:
            if cv2.contourArea(contour) >= self.min_area:
                rects.append(cv2.boundingRect(contour))

        # Update object trackers
        objects = self.tracker.update(rects)

        # Update vehicle information and draw
        current_time = time.time()
        for objectID, centroid in objects.items():
            if objectID not in self.vehicle_info:
                self.vehicle_info[objectID] = {
                    'last_position': centroid,
                    'last_update': current_time,
                    'speed': 0,
                    'avg_speed': 0,
                    'color': 'unknown',
                    'speed_history': [],
                    'positions': [centroid],
                    'timestamps': [current_time],
                    'first_detected': current_time,
                    'bbox': None  # Will store the bounding box for color detection
                }
            else:
                # Store position and timestamp
                self.vehicle_info[objectID]['positions'].append(centroid)
                self.vehicle_info[objectID]['timestamps'].append(current_time)

                # Keep only recent positions (last 10)
                if len(self.vehicle_info[objectID]['positions']) > 10:
                    self.vehicle_info[objectID]['positions'] = self.vehicle_info[objectID]['positions'][-10:]
                    self.vehicle_info[objectID]['timestamps'] = self.vehicle_info[objectID]['timestamps'][-10:]

                # Calculate speed only if we've been tracking for minimum time
                tracking_time = current_time - self.vehicle_info[objectID]['first_detected']
                if tracking_time >= self.min_tracking_time:
                    # Calculate speed using the last few positions for better accuracy
                    positions = self.vehicle_info[objectID]['positions']
                    timestamps = self.vehicle_info[objectID]['timestamps']

                    # Use multiple points if available for more stable measurement
                    if len(positions) >= 3:
                        # Calculate speed using the first and last positions in our recent history
                        time_diff = timestamps[-1] - timestamps[0]
                        speed = self.calculate_speed(positions[0], positions[-1], time_diff)
                    else:
                        # Fall back to simple calculation if we don't have enough history
                        time_diff = current_time - self.vehicle_info[objectID]['last_update']
                        speed = self.calculate_speed(
                            self.vehicle_info[objectID]['last_position'],
                            centroid,
                            time_diff
                        )

                    # Apply smoothing
                    if speed > 0:
                        smoothed_speed = self.smooth_speed(objectID, speed)
                        self.vehicle_info[objectID]['speed'] = smoothed_speed

                # Update last position and time
                self.vehicle_info[objectID]['last_position'] = centroid
                self.vehicle_info[objectID]['last_update'] = current_time

                # Find the bounding box for this object
                for rect in rects:
                    x, y, w, h = rect
                    rect_center = (x + w//2, y + h//2)

                    # Check if this rectangle's center is close to the tracked object's centroid
                    distance = np.sqrt((centroid[0] - rect_center[0])**2 + (centroid[1] - rect_center[1])**2)
                    if distance < 50:  # Threshold for matching
                        # Store the bounding box
                        self.vehicle_info[objectID]['bbox'] = rect

                        # Detect color if we haven't already or if we're still tracking for a while
                        if self.vehicle_info[objectID]['color'] == 'unknown' or tracking_time < 2.0:
                            color = self.detect_color(frame, rect)
                            if color != 'unknown':
                                self.vehicle_info[objectID]['color'] = color
                        break

                # Draw vehicle info
                x, y = centroid
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
                cv2.putText(frame, f"ID {objectID}", (x - 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame, f"Speed: {self.vehicle_info[objectID]['speed']:.1f} km/h",
                    (x - 10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(frame, f"Color: {self.vehicle_info[objectID]['color']}",
                    (x - 10, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Check for speeding
                if speed > self.speed_limit:
                    try:
                        # Check if the database has the new method signature
                        if hasattr(self.db, 'add_vehicle') and callable(getattr(self.db, 'add_vehicle')):
                            # Try with the new method signature first
                            try:
                                # Get the detected color and average speed
                                vehicle_color = self.vehicle_info[objectID]['color']
                                if vehicle_color == 'unknown':
                                    vehicle_color = "UNKNOWN"

                                avg_speed = self.vehicle_info[objectID]['avg_speed']
                                if avg_speed == 0:
                                    avg_speed = speed

                                self.db.add_vehicle(
                                    plate_number=f"UNKNOWN_{objectID}",
                                    color=vehicle_color.upper(),
                                    speed=int(avg_speed),
                                    vehicle_type="Detected"
                                )
                            except TypeError:
                                # Fall back to old method signature
                                vehicle_color = self.vehicle_info[objectID]['color']
                                if vehicle_color == 'unknown':
                                    vehicle_color = "UNKNOWN"

                                avg_speed = self.vehicle_info[objectID]['avg_speed']
                                if avg_speed == 0:
                                    avg_speed = speed

                                self.db.add_vehicle(
                                    plate_number=f"UNKNOWN_{objectID}",
                                    color=vehicle_color.upper(),
                                    speed=int(avg_speed)
                                )

                        # Add violation
                        avg_speed = self.vehicle_info[objectID]['avg_speed']
                        if avg_speed == 0:
                            avg_speed = speed

                        self.db.add_violation(
                            plate_number=f"UNKNOWN_{objectID}",
                            violation_type="Speeding",
                            speed=int(avg_speed),
                            fine_amount=1000
                        )
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error adding violation: {str(e)}")

        return frame

    def process_video(self):
        try:
            # Auto-calibrate based on video resolution
            self.auto_calibrate()

            # Create window
            cv2.namedWindow('Traffic Analysis')

            # Create a simple UI with instructions
            instructions = np.zeros((50, 800, 3), dtype=np.uint8)
            cv2.putText(instructions, "Press 'q' to quit", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            while self.cap.isOpened():
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        break

                    processed_frame = self.process_frame(frame)

                    # Add speed limit info
                    cv2.putText(processed_frame, f"Speed Limit: {self.speed_limit} km/h", (20, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    # Display the frame with instructions
                    display_frame = np.vstack([instructions, processed_frame])
                    cv2.imshow('Traffic Analysis', display_frame)

                    # Handle key presses
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                except Exception:
                    # If there's an error processing a frame, just continue to the next one
                    continue

            self.cap.release()
            cv2.destroyAllWindows()
        except Exception:
            # If there's any error, make sure to release resources
            if hasattr(self, 'cap') and self.cap.isOpened():
                self.cap.release()
            cv2.destroyAllWindows()

    def __del__(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()