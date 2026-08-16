"""
Vehicle Tracking System - Solves the "double counting" problem
This is the most critical improvement for accuracy
"""

import numpy as np
import cv2
from collections import OrderedDict, defaultdict, deque
from scipy.spatial import distance as dist
import time

class CentroidTracker:
    """
    Centroid-based object tracker to maintain vehicle identity across frames
    """
    def __init__(self, max_disappeared=30, max_distance=80):
        # Initialize the next unique object ID
        self.next_object_id = 0
        
        # Store centroids of existing objects
        self.objects = OrderedDict()
        
        # Store number of frames object has been marked as "disappeared"
        self.disappeared = OrderedDict()
        
        # Maximum number of consecutive frames object can be marked as disappeared
        self.max_disappeared = max_disappeared
        
        # Maximum distance between centroids to associate object
        self.max_distance = max_distance
        
        # Store object history for smoothing
        self.object_history = defaultdict(lambda: deque(maxlen=10))
        
    def register(self, centroid, bbox, class_id, confidence):
        """Register a new object with given centroid"""
        self.objects[self.next_object_id] = {
            'centroid': centroid,
            'bbox': bbox,
            'class_id': class_id,
            'confidence': confidence,
            'first_seen': time.time(),
            'last_seen': time.time(),
            'frame_count': 1
        }
        self.disappeared[self.next_object_id] = 0
        self.object_history[self.next_object_id].append(centroid)
        self.next_object_id += 1
        
    def deregister(self, object_id):
        """Delete an object ID from both dictionaries"""
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.object_history:
            del self.object_history[object_id]
            
    def update(self, detections):
        """
        Update tracker with new detections
        detections: list of [x1, y1, x2, y2, confidence, class_id]
        """
        # Check if the list of input bounding box rectangles is empty
        if len(detections) == 0:
            # Mark all existing objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                # Remove object if it has been disappeared for too long
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
                    
            return self.get_objects()
        
        # Initialize array of input centroids for current frame
        input_centroids = []
        input_data = []
        
        for detection in detections:
            x1, y1, x2, y2, confidence, class_id = detection
            cx = int((x1 + x2) / 2.0)
            cy = int((y1 + y2) / 2.0)
            input_centroids.append((cx, cy))
            input_data.append({
                'centroid': (cx, cy),
                'bbox': (x1, y1, x2, y2),
                'class_id': class_id,
                'confidence': confidence
            })
            
        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for data in input_data:
                self.register(data['centroid'], data['bbox'], 
                            data['class_id'], data['confidence'])
        else:
            # Grab centroids of existing objects
            object_centroids = [obj['centroid'] for obj in self.objects.values()]
            object_ids = list(self.objects.keys())
            
            # Compute distance matrix between existing and input centroids
            D = dist.cdist(np.array(object_centroids), input_centroids)
            
            # Find minimum values and sort by distance
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            # Keep track of used row and column indices
            used_row_indices = set()
            used_col_indices = set()
            
            # Loop over the combination of (row, column) index tuples
            for (row, col) in zip(rows, cols):
                # Ignore if already examined
                if row in used_row_indices or col in used_col_indices:
                    continue
                    
                # If distance is greater than maximum, ignore
                if D[row, col] > self.max_distance:
                    continue
                    
                # Update existing object
                object_id = object_ids[row]
                data = input_data[col]
                
                # Update object information
                self.objects[object_id].update({
                    'centroid': data['centroid'],
                    'bbox': data['bbox'],
                    'class_id': data['class_id'],
                    'confidence': data['confidence'],
                    'last_seen': time.time(),
                    'frame_count': self.objects[object_id]['frame_count'] + 1
                })
                
                # Reset disappeared counter
                self.disappeared[object_id] = 0
                
                # Add to history for smoothing
                self.object_history[object_id].append(data['centroid'])
                
                # Mark indices as used
                used_row_indices.add(row)
                used_col_indices.add(col)
                
            # Handle unmatched detections and objects
            unused_row_indices = set(range(0, D.shape[0])).difference(used_row_indices)
            unused_col_indices = set(range(0, D.shape[1])).difference(used_col_indices)
            
            # If more objects than detections, mark objects as disappeared
            if D.shape[0] >= D.shape[1]:
                for row in unused_row_indices:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    
                    # Remove if disappeared too long
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
                        
            # If more detections than objects, register new objects
            else:
                for col in unused_col_indices:
                    data = input_data[col]
                    self.register(data['centroid'], data['bbox'],
                                data['class_id'], data['confidence'])
                    
        return self.get_objects()
    
    def get_objects(self):
        """Return current objects with smoothed positions"""
        smoothed_objects = {}
        
        for object_id, obj_data in self.objects.items():
            # Apply smoothing if enough history
            if len(self.object_history[object_id]) >= 3:
                # Use median of recent positions for smoothing
                recent_positions = list(self.object_history[object_id])[-5:]
                x_coords = [pos[0] for pos in recent_positions]
                y_coords = [pos[1] for pos in recent_positions]
                
                smoothed_centroid = (
                    int(np.median(x_coords)),
                    int(np.median(y_coords))
                )
            else:
                smoothed_centroid = obj_data['centroid']
                
            smoothed_objects[object_id] = {
                **obj_data,
                'smoothed_centroid': smoothed_centroid,
                'track_length': len(self.object_history[object_id]),
                'is_stable': len(self.object_history[object_id]) >= 5
            }
            
        return smoothed_objects

class VehicleCounter:
    """
    Accurate vehicle counting using tracking
    """
    def __init__(self, counting_line=None):
        self.counted_vehicles = set()
        self.counting_line = counting_line  # (x1, y1, x2, y2)
        self.vehicle_counts = defaultdict(int)
        self.total_count = 0
        
        # Vehicle class mapping
        self.class_names = {
            0: 'person',
            1: 'bicycle', 
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck'
        }
        
    def set_counting_line(self, line_coords):
        """Set the counting line coordinates"""
        self.counting_line = line_coords
        
    def point_line_distance(self, point, line):
        """Calculate distance from point to line"""
        x0, y0 = point
        x1, y1, x2, y2 = line
        
        # Line equation: ax + by + c = 0
        a = y2 - y1
        b = x1 - x2
        c = x2 * y1 - x1 * y2
        
        distance = abs(a * x0 + b * y0 + c) / np.sqrt(a**2 + b**2)
        return distance
        
    def crossed_line(self, object_history, threshold=20):
        """Check if object crossed the counting line"""
        if not self.counting_line or len(object_history) < 2:
            return False
            
        # Check last few positions
        recent_positions = list(object_history)[-5:]
        
        # Simple crossing detection based on line distance
        distances = [self.point_line_distance(pos, self.counting_line) 
                    for pos in recent_positions]
        
        # Check if object moved from one side to another
        if len(distances) >= 2:
            return min(distances) < threshold and max(distances) > threshold
            
        return False
        
    def update_counts(self, tracked_objects):
        """Update vehicle counts based on tracked objects"""
        current_frame_counts = defaultdict(int)
        
        for object_id, obj_data in tracked_objects.items():
            class_id = obj_data['class_id']
            vehicle_type = self.class_names.get(class_id, 'unknown')
            
            # Only count vehicles (not persons)
            if class_id in [1, 2, 3, 5, 7]:  # bicycle, car, motorcycle, bus, truck
                current_frame_counts[vehicle_type] += 1
                
                # Check if this vehicle crossed counting line
                if (self.counting_line and 
                    object_id not in self.counted_vehicles and
                    obj_data.get('is_stable', False)):
                    
                    object_history = obj_data.get('track_history', [])
                    if self.crossed_line(object_history):
                        self.counted_vehicles.add(object_id)
                        self.vehicle_counts[vehicle_type] += 1
                        self.total_count += 1
                        
        return current_frame_counts
    
    def get_counts(self):
        """Get current vehicle counts"""
        return {
            'current_frame': dict(self.vehicle_counts),
            'total_counted': self.total_count,
            'unique_vehicles': len(self.counted_vehicles)
        }

class TemporalSmoother:
    """
    Apply temporal smoothing to reduce flickering results
    """
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.history = {
            'total_vehicles': deque(maxlen=window_size),
            'vehicle_counts': deque(maxlen=window_size),
            'density_level': deque(maxlen=window_size)
        }
        
    def smooth_results(self, current_results):
        """Apply smoothing to current results"""
        # Add current results to history
        self.history['total_vehicles'].append(current_results.get('total_vehicles', 0))
        self.history['vehicle_counts'].append(current_results.get('vehicle_counts', {}))
        self.history['density_level'].append(current_results.get('density_level', 'Low'))
        
        # Calculate smoothed values
        smoothed_results = current_results.copy()
        
        # Smooth total vehicle count
        if len(self.history['total_vehicles']) >= 3:
            smoothed_results['total_vehicles'] = int(
                np.median(list(self.history['total_vehicles']))
            )
            
        # Smooth vehicle counts by type
        if len(self.history['vehicle_counts']) >= 3:
            smoothed_counts = defaultdict(list)
            for counts in self.history['vehicle_counts']:
                for vehicle_type, count in counts.items():
                    smoothed_counts[vehicle_type].append(count)
                    
            smoothed_vehicle_counts = {}
            for vehicle_type, count_history in smoothed_counts.items():
                smoothed_vehicle_counts[vehicle_type] = int(np.median(count_history))
                
            smoothed_results['vehicle_counts'] = smoothed_vehicle_counts
            
        # Smooth density level (use mode)
        if len(self.history['density_level']) >= 3:
            density_history = list(self.history['density_level'])
            smoothed_results['density_level'] = max(set(density_history), 
                                                   key=density_history.count)
            
        return smoothed_results

# Example usage and testing
if __name__ == "__main__":
    # Test the tracking system
    tracker = CentroidTracker()
    counter = VehicleCounter()
    smoother = TemporalSmoother()
    
    print("Vehicle Tracking System Initialized")
    print("=" * 50)
    
    # Simulate detections for testing
    test_detections = [
        [100, 100, 150, 150, 0.9, 2],  # car
        [200, 200, 250, 250, 0.8, 3],  # motorcycle
        [300, 300, 400, 400, 0.95, 5]  # bus
    ]
    
    # Update tracker
    tracked_objects = tracker.update(test_detections)
    
    print(f"Tracked Objects: {len(tracked_objects)}")
    for obj_id, obj_data in tracked_objects.items():
        print(f"  ID {obj_id}: {obj_data['class_id']} at {obj_data['centroid']}")
        
    # Update counter
    frame_counts = counter.update_counts(tracked_objects)
    print(f"Frame Counts: {frame_counts}")
    
    # Test smoothing
    test_results = {
        'total_vehicles': len(tracked_objects),
        'vehicle_counts': dict(frame_counts),
        'density_level': 'Medium'
    }
    
    smoothed = smoother.smooth_results(test_results)
    print(f"Smoothed Results: {smoothed}")
    
    print("\n" + "=" * 50)
    print("✅ Tracking system ready for integration!")