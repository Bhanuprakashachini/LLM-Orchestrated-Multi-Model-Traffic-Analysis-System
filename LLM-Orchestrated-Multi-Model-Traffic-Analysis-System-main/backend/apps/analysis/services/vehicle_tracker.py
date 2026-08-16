"""
Vehicle Tracking Service using DeepSORT-like algorithm
Provides trajectory analysis and prevents double counting
"""
import numpy as np
import cv2
from typing import Dict, List, Any, Optional, Tuple
import logging
from collections import defaultdict, deque
import time

logger = logging.getLogger(__name__)


class VehicleTracker:
    """
    Vehicle tracking service for trajectory analysis and counting
    """
    
    def __init__(self, max_disappeared: int = 30, max_distance: float = 100):
        """
        Initialize the vehicle tracker
        
        Args:
            max_disappeared: Maximum frames a vehicle can disappear before removal
            max_distance: Maximum distance for matching detections to tracks
        """
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        
        # Tracking state
        self.next_object_id = 0
        self.objects = {}  # object_id -> centroid
        self.disappeared = {}  # object_id -> disappeared_count
        self.trajectories = {}  # object_id -> list of centroids
        self.vehicle_classes = {}  # object_id -> vehicle_class
        self.confidences = {}  # object_id -> confidence_history
        
        # Speed estimation
        self.previous_centroids = {}  # object_id -> previous_centroid
        self.speeds = {}  # object_id -> estimated_speed
        self.timestamps = {}  # object_id -> timestamp
        
        # Counting zones (can be configured)
        self.counting_lines = []  # List of counting line coordinates
        self.vehicle_counts = defaultdict(int)  # Direction -> count
        self.crossed_vehicles = set()  # Track which vehicles have been counted
        
    def add_counting_line(self, start_point: Tuple[int, int], end_point: Tuple[int, int], direction: str):
        """Add a counting line for traffic flow analysis"""
        self.counting_lines.append({
            'start': start_point,
            'end': end_point,
            'direction': direction
        })
    
    def update(self, detections: List[Dict[str, Any]], frame_timestamp: float = None) -> Dict[str, Any]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of detection dictionaries with bbox, class, confidence
            frame_timestamp: Timestamp of current frame
            
        Returns:
            Dictionary with tracking results
        """
        if frame_timestamp is None:
            frame_timestamp = time.time()
        
        # Extract centroids from detections
        input_centroids = []
        detection_classes = []
        detection_confidences = []
        
        for detection in detections:
            bbox = detection['bbox']
            center_x = (bbox['x1'] + bbox['x2']) // 2
            center_y = (bbox['y1'] + bbox['y2']) // 2
            
            input_centroids.append((center_x, center_y))
            detection_classes.append(detection['class'])
            detection_confidences.append(detection['confidence'])
        
        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for i, centroid in enumerate(input_centroids):
                self._register_object(centroid, detection_classes[i], 
                                    detection_confidences[i], frame_timestamp)
        
        # If no input centroids, mark all existing objects as disappeared
        elif len(input_centroids) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                # Remove objects that have disappeared too long
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister_object(object_id)
        
        # Otherwise, match detections to existing objects
        else:
            self._match_detections_to_objects(input_centroids, detection_classes, 
                                            detection_confidences, frame_timestamp)
        
        # Update speeds and trajectories
        self._update_speeds_and_trajectories(frame_timestamp)
        
        # Check counting lines
        self._check_counting_lines()
        
        return self._get_tracking_results()
    
    def _register_object(self, centroid: Tuple[int, int], vehicle_class: str, 
                        confidence: float, timestamp: float):
        """Register a new object"""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.trajectories[self.next_object_id] = deque([centroid], maxlen=30)
        self.vehicle_classes[self.next_object_id] = vehicle_class
        self.confidences[self.next_object_id] = deque([confidence], maxlen=10)
        self.timestamps[self.next_object_id] = timestamp
        self.previous_centroids[self.next_object_id] = centroid
        
        logger.debug(f"Registered new {vehicle_class} with ID {self.next_object_id}")
        self.next_object_id += 1
    
    def _deregister_object(self, object_id: int):
        """Remove an object from tracking"""
        logger.debug(f"Deregistered object ID {object_id}")
        del self.objects[object_id]
        del self.disappeared[object_id]
        del self.trajectories[object_id]
        del self.vehicle_classes[object_id]
        del self.confidences[object_id]
        if object_id in self.timestamps:
            del self.timestamps[object_id]
        if object_id in self.previous_centroids:
            del self.previous_centroids[object_id]
        if object_id in self.speeds:
            del self.speeds[object_id]
    
    def _match_detections_to_objects(self, input_centroids: List[Tuple[int, int]], 
                                   detection_classes: List[str], 
                                   detection_confidences: List[float],
                                   timestamp: float):
        """Match new detections to existing tracked objects"""
        # Compute distance matrix
        object_centroids = list(self.objects.values())
        object_ids = list(self.objects.keys())
        
        if len(object_centroids) > 0 and len(input_centroids) > 0:
            # Calculate distances between all pairs
            distances = np.linalg.norm(
                np.array(object_centroids)[:, np.newaxis] - np.array(input_centroids), 
                axis=2
            )
            
            # Find the minimum values and sort by distance
            rows = distances.min(axis=1).argsort()
            cols = distances.argmin(axis=1)[rows]
            
            # Keep track of used row and column indices
            used_rows = set()
            used_cols = set()
            
            # Update existing objects
            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                if distances[row, col] <= self.max_distance:
                    object_id = object_ids[row]
                    
                    # Update object
                    self.objects[object_id] = input_centroids[col]
                    self.disappeared[object_id] = 0
                    self.trajectories[object_id].append(input_centroids[col])
                    self.confidences[object_id].append(detection_confidences[col])
                    self.timestamps[object_id] = timestamp
                    
                    # Update class if confidence is higher
                    if detection_confidences[col] > max(self.confidences[object_id]):
                        self.vehicle_classes[object_id] = detection_classes[col]
                    
                    used_rows.add(row)
                    used_cols.add(col)
            
            # Handle unmatched detections and objects
            unused_rows = set(range(0, distances.shape[0])).difference(used_rows)
            unused_cols = set(range(0, distances.shape[1])).difference(used_cols)
            
            # Mark unmatched objects as disappeared
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self._deregister_object(object_id)
            
            # Register new objects for unmatched detections
            for col in unused_cols:
                self._register_object(input_centroids[col], detection_classes[col], 
                                    detection_confidences[col], timestamp)
    
    def _update_speeds_and_trajectories(self, timestamp: float):
        """Update speed estimates for tracked objects"""
        for object_id in self.objects:
            if object_id in self.previous_centroids and object_id in self.timestamps:
                # Calculate distance moved
                current_pos = self.objects[object_id]
                previous_pos = self.previous_centroids[object_id]
                previous_time = self.timestamps.get(object_id, timestamp)
                
                distance = np.linalg.norm(np.array(current_pos) - np.array(previous_pos))
                time_diff = timestamp - previous_time
                
                if time_diff > 0:
                    # Speed in pixels per second (can be converted to real units with calibration)
                    speed = distance / time_diff
                    self.speeds[object_id] = speed
            
            # Update previous position
            self.previous_centroids[object_id] = self.objects[object_id]
    
    def _check_counting_lines(self):
        """Check if any vehicles have crossed counting lines"""
        for object_id, trajectory in self.trajectories.items():
            if len(trajectory) < 2:
                continue
            
            # Check each counting line
            for line in self.counting_lines:
                if self._line_crossed(trajectory, line) and object_id not in self.crossed_vehicles:
                    self.vehicle_counts[line['direction']] += 1
                    self.crossed_vehicles.add(object_id)
                    
                    vehicle_class = self.vehicle_classes.get(object_id, 'unknown')
                    logger.info(f"Vehicle {object_id} ({vehicle_class}) crossed {line['direction']} line")
    
    def _line_crossed(self, trajectory: deque, line: Dict[str, Any]) -> bool:
        """Check if trajectory crosses a counting line"""
        if len(trajectory) < 2:
            return False
        
        # Simple line intersection check
        p1, p2 = trajectory[-2], trajectory[-1]
        line_start, line_end = line['start'], line['end']
        
        return self._lines_intersect(p1, p2, line_start, line_end)
    
    def _lines_intersect(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                        p3: Tuple[int, int], p4: Tuple[int, int]) -> bool:
        """Check if two line segments intersect"""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    def _get_tracking_results(self) -> Dict[str, Any]:
        """Get current tracking results"""
        tracked_objects = []
        
        for object_id, centroid in self.objects.items():
            vehicle_class = self.vehicle_classes.get(object_id, 'unknown')
            avg_confidence = np.mean(list(self.confidences.get(object_id, [0.5])))
            speed = self.speeds.get(object_id, 0)
            trajectory = list(self.trajectories.get(object_id, []))
            
            tracked_objects.append({
                'id': object_id,
                'centroid': centroid,
                'class': vehicle_class,
                'confidence': avg_confidence,
                'speed': speed,
                'trajectory': trajectory,
                'trajectory_length': len(trajectory)
            })
        
        # Count vehicles by class
        class_counts = defaultdict(int)
        for obj in tracked_objects:
            class_counts[obj['class']] += 1
        
        return {
            'tracked_objects': tracked_objects,
            'total_tracked': len(tracked_objects),
            'class_counts': dict(class_counts),
            'flow_counts': dict(self.vehicle_counts),
            'average_speed': np.mean(list(self.speeds.values())) if self.speeds else 0,
            'active_trajectories': len([t for t in self.trajectories.values() if len(t) > 5])
        }
    
    def draw_tracks(self, frame: np.ndarray, tracking_results: Dict[str, Any]) -> np.ndarray:
        """Draw tracking visualization on frame"""
        annotated_frame = frame.copy()
        
        # Colors for different vehicle classes
        colors = {
            'car': (0, 255, 0),
            'motorcycle': (255, 0, 0),
            'bus': (0, 0, 255),
            'truck': (255, 255, 0),
            'bicycle': (255, 0, 255),
            'unknown': (128, 128, 128)
        }
        
        for obj in tracking_results['tracked_objects']:
            centroid = obj['centroid']
            object_id = obj['id']
            vehicle_class = obj['class']
            speed = obj['speed']
            trajectory = obj['trajectory']
            
            color = colors.get(vehicle_class, colors['unknown'])
            
            # Draw centroid
            cv2.circle(annotated_frame, centroid, 5, color, -1)
            
            # Draw ID and info
            label = f"ID:{object_id} {vehicle_class} {speed:.1f}px/s"
            cv2.putText(annotated_frame, label, (centroid[0] - 50, centroid[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw trajectory
            if len(trajectory) > 1:
                points = np.array(trajectory, dtype=np.int32)
                cv2.polylines(annotated_frame, [points], False, color, 2)
        
        # Draw counting lines
        for line in self.counting_lines:
            cv2.line(annotated_frame, line['start'], line['end'], (0, 255, 255), 3)
            
            # Draw direction label
            mid_point = ((line['start'][0] + line['end'][0]) // 2,
                        (line['start'][1] + line['end'][1]) // 2)
            cv2.putText(annotated_frame, line['direction'], mid_point,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return annotated_frame
    
    def reset(self):
        """Reset tracker state"""
        self.next_object_id = 0
        self.objects.clear()
        self.disappeared.clear()
        self.trajectories.clear()
        self.vehicle_classes.clear()
        self.confidences.clear()
        self.previous_centroids.clear()
        self.speeds.clear()
        self.timestamps.clear()
        self.vehicle_counts.clear()
        self.crossed_vehicles.clear()
        
        logger.info("Vehicle tracker reset")