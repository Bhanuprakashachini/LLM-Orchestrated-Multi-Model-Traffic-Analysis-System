"""
YOLO Model Processor for Traffic Violations
Supports YOLOv8s, YOLOv11s, and YOLOv12s models
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os
import time
from typing import Dict, List, Tuple, Optional


class YOLOProcessor:
    """YOLO model processor for vehicle detection"""
    
    # Available models (only the 3 specified) - centralized paths
    AVAILABLE_MODELS = {
        'yolov8s': os.path.join('backend', 'models', 'yolov8s.pt'),
        'yolo11s': os.path.join('backend', 'models', 'yolo11s.pt'), 
        'yolo12s': os.path.join('backend', 'models', 'yolo12s.pt')
    }
    
    # Vehicle classes from COCO dataset
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle', 
        5: 'bus',
        7: 'truck'
    }
    
    def __init__(self, model_name: str = 'yolov8s', confidence_threshold: float = 0.15):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold  # Lowered for better detection
        self.model = None
        self.model_path = None
        
        self.load_model()
    
    def load_model(self):
        """Load the specified YOLO model"""
        if self.model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model {self.model_name} not available. Choose from: {list(self.AVAILABLE_MODELS.keys())}")
        
        model_filename = self.AVAILABLE_MODELS[self.model_name]
        
        # Try different possible locations for the model
        possible_paths = [
            model_filename,  # Current directory
            os.path.join('models', model_filename),  # models directory
            os.path.join('backend', 'models', model_filename),  # backend/models
            os.path.join('..', model_filename),  # Parent directory
            os.path.join('Traffic detection system', model_filename),  # Traffic detection system folder
        ]
        
        # Check centralized models directory first
        centralized_models = [
            f'models/{self.model_name}.pt',
            f'backend/models/{self.model_name}.pt'
        ]
        
        # Also check root directory for the models (legacy support)
        root_models = [
            f'{self.model_name}.pt'
        ]
        
        for root_model in root_models:
            if os.path.exists(root_model) and model_filename == root_model:
                possible_paths.insert(0, root_model)
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if model_path is None:
            print(f"⚠️ Model file {model_filename} not found in any of these locations:")
            for path in possible_paths:
                print(f"   - {path}")
            print(f"📥 Downloading {self.model_name} model...")
            # YOLO will automatically download if not found
            model_path = model_filename
        
        try:
            print(f"🤖 Loading {self.model_name} model from: {model_path}")
            self.model = YOLO(model_path)
            self.model_path = model_path
            print(f"✅ {self.model_name} model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading {self.model_name} model: {e}")
            raise
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict]:
        """Detect vehicles in a frame with improved accuracy"""
        if self.model is None:
            return []
        
        try:
            # Run YOLO detection with optimized parameters
            results = self.model(frame, conf=self.confidence_threshold, iou=0.4, verbose=False)
            
            detections = []
            
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Only process vehicle classes with improved filtering
                        if class_id in self.VEHICLE_CLASSES and confidence > self.confidence_threshold:
                            vehicle_type = self.VEHICLE_CLASSES[class_id]
                            
                            # Filter out very small detections (likely false positives)
                            bbox_width = x2 - x1
                            bbox_height = y2 - y1
                            bbox_area = bbox_width * bbox_height
                            
                            # Minimum size filtering based on image dimensions
                            frame_area = frame.shape[0] * frame.shape[1]
                            min_area_ratio = 0.0005  # Minimum 0.05% of frame area
                            
                            if bbox_area < frame_area * min_area_ratio:
                                continue  # Skip very small detections
                            
                            # Aspect ratio filtering (vehicles should have reasonable proportions)
                            aspect_ratio = bbox_width / bbox_height if bbox_height > 0 else 0
                            if aspect_ratio < 0.3 or aspect_ratio > 4.0:
                                continue  # Skip unrealistic aspect ratios
                            
                            detection = {
                                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                'confidence': float(confidence),
                                'class_id': class_id,
                                'vehicle_type': vehicle_type,
                                'center_x': float((x1 + x2) / 2),
                                'center_y': float((y1 + y2) / 2),
                                'width': float(bbox_width),
                                'height': float(bbox_height),
                                'area': float(bbox_area),
                                'aspect_ratio': float(aspect_ratio)
                            }
                            
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"❌ Error in vehicle detection: {e}")
            return []
    
    def annotate_frame(self, frame: np.ndarray, detections: List[Dict], 
                      speeds: Dict[str, float] = None, speed_limit: float = 50) -> np.ndarray:
        """Annotate frame with detection results and speeds"""
        annotated_frame = frame.copy()
        
        if speeds is None:
            speeds = {}
        
        for detection in detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox
            vehicle_type = detection['vehicle_type']
            confidence = detection['confidence']
            
            # Create vehicle ID for speed lookup
            center_x = int(detection['center_x'])
            center_y = int(detection['center_y'])
            vehicle_id = f"{vehicle_type}_{center_x//30}_{center_y//30}"
            
            # Get speed for this vehicle
            speed = speeds.get(vehicle_id, 0)
            
            # Determine color based on speed
            if speed == 0:
                color = (128, 128, 128)  # Gray for stationary
                speed_text = "0 km/h (STATIONARY)"
                status_text = "STATIONARY"
            elif speed > speed_limit:
                color = (0, 0, 255)  # Red for speeding
                speed_text = f"{speed:.1f} km/h (SPEEDING!)"
                status_text = "SPEEDING"
            else:
                color = (0, 255, 0)  # Green for normal
                speed_text = f"{speed:.1f} km/h (NORMAL)"
                status_text = "NORMAL"
            
            # Draw bounding box
            thickness = 4 if speed > speed_limit else 2
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
            
            # Vehicle type and confidence
            vehicle_display = vehicle_type.upper()
            cv2.putText(annotated_frame, f"{vehicle_display} ({confidence:.2f})", 
                       (int(x1), int(y1)-70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Speed display (large and prominent)
            cv2.putText(annotated_frame, speed_text, 
                       (int(x1), int(y1)-40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
            
            # Status
            cv2.putText(annotated_frame, f"Status: {status_text}", 
                       (int(x1), int(y1)-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return annotated_frame
    
    def add_info_overlay(self, frame: np.ndarray, frame_count: int, 
                        vehicle_counts: Dict, violation_stats: Dict, 
                        speed_limit: float) -> np.ndarray:
        """Add information overlay to frame"""
        overlay_height = 120
        cv2.rectangle(frame, (10, 10), (700, overlay_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (700, overlay_height), (255, 255, 255), 2)
        
        # Title
        cv2.putText(frame, "TRAFFIC VIOLATION DETECTION SYSTEM", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Settings and info
        cv2.putText(frame, f"Model: {self.model_name.upper()} | Speed Limit: {speed_limit} km/h | ALL VEHICLES SHOW SPEEDS", 
                   (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Vehicle counts
        total_vehicles = vehicle_counts.get('total', 0)
        violations = violation_stats.get('total_violations', 0)
        cv2.putText(frame, f"Vehicles: {total_vehicles} | Violations: {violations} | Frame: {frame_count}", 
                   (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Detailed counts
        cars = vehicle_counts.get('cars', 0)
        bikes = vehicle_counts.get('bikes', 0)
        buses = vehicle_counts.get('buses', 0)
        trucks = vehicle_counts.get('trucks', 0)
        cv2.putText(frame, f"Cars: {cars} | Bikes: {bikes} | Buses: {buses} | Trucks: {trucks}", 
                   (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Legend
        cv2.putText(frame, "GREEN=Normal | RED=Speeding | GRAY=Stationary | GUARANTEED SPEED DISPLAY", 
                   (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'model_path': self.model_path,
            'confidence_threshold': self.confidence_threshold,
            'available_models': list(self.AVAILABLE_MODELS.keys()),
            'vehicle_classes': self.VEHICLE_CLASSES
        }
    
    def switch_model(self, new_model_name: str):
        """Switch to a different YOLO model"""
        if new_model_name in self.AVAILABLE_MODELS:
            self.model_name = new_model_name
            self.load_model()
        else:
            raise ValueError(f"Model {new_model_name} not available")
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for detections"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
        else:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")