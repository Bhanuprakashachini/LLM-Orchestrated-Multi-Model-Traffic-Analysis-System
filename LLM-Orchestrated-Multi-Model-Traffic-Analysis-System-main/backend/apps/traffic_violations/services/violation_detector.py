"""
Traffic Violation Detection Service
Combines speed detection, helmet detection, and other traffic violations
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np

from .guaranteed_speed_calculator import GuaranteedSpeedCalculator
from .helmet_detector import HelmetDetector
from .yolo_processor import YOLOProcessor


class ViolationDetector:
    """Main traffic violation detection system"""
    
    def __init__(self, model_name: str = 'yolov8s', speed_limit: float = 50.0):
        self.speed_limit = speed_limit
        self.model_name = model_name
        
        # Initialize components
        self.yolo_processor = YOLOProcessor(model_name)
        self.speed_calculator = GuaranteedSpeedCalculator()
        self.helmet_detector = HelmetDetector()
        
        # Tracking data
        self.frame_count = 0
        self.session_violations = []
        self.session_statistics = {
            'total_violations': 0,
            'speed_violations': 0,
            'helmet_violations': 0,
            'red_light_violations': 0,
            'vehicle_counts': {
                'cars': 0,
                'bikes': 0,
                'buses': 0,
                'trucks': 0,
                'total': 0
            },
            'processing_stats': {
                'frames_processed': 0,
                'avg_processing_time': 0.0,
                'total_processing_time': 0.0
            }
        }
    
    def process_frame(self, frame: np.ndarray, timestamp: Optional[str] = None) -> Dict:
        """Process a single frame for violations"""
        start_time = time.time()
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        self.frame_count += 1
        self.speed_calculator.update_frame_count()
        
        # Detect vehicles
        detections = self.yolo_processor.detect_vehicles(frame)
        
        # Process each detection
        frame_violations = []
        frame_vehicle_counts = {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
        vehicle_speeds = {}
        
        current_time = time.time()
        
        for detection in detections:
            vehicle_type = detection['vehicle_type']
            bbox = detection['bbox']
            
            # Update vehicle counts
            if vehicle_type == 'car':
                frame_vehicle_counts['cars'] += 1
            elif vehicle_type == 'motorcycle':
                frame_vehicle_counts['bikes'] += 1
            elif vehicle_type == 'bus':
                frame_vehicle_counts['buses'] += 1
            elif vehicle_type == 'truck':
                frame_vehicle_counts['trucks'] += 1
            
            frame_vehicle_counts['total'] += 1
            
            # Create vehicle ID for tracking
            center_x = int(detection['center_x'])
            center_y = int(detection['center_y'])
            vehicle_id = f"{vehicle_type}_{center_x//30}_{center_y//30}"
            
            # Calculate speed
            speed, speed_method = self.speed_calculator.calculate_guaranteed_speed(
                vehicle_id, bbox, current_time
            )
            vehicle_speeds[vehicle_id] = speed
            
            # Check for speed violations
            if speed > self.speed_limit and speed > 0:
                speed_violation = self._create_speed_violation(
                    detection, speed, self.frame_count, timestamp
                )
                frame_violations.append(speed_violation)
            
            # Check for helmet violations (motorcycles only)
            if vehicle_type == 'motorcycle':
                helmet_result = self.helmet_detector.detect_helmet_multi_method(frame, bbox)
                helmet_violation = self.helmet_detector.create_helmet_violation(
                    detection, helmet_result, self.frame_count, timestamp
                )
                if helmet_violation:
                    frame_violations.append(helmet_violation)
        
        # Update session statistics
        self._update_session_statistics(frame_vehicle_counts, frame_violations)
        
        # Annotate frame
        annotated_frame = self.yolo_processor.annotate_frame(
            frame, detections, vehicle_speeds, self.speed_limit
        )
        
        # Add info overlay
        annotated_frame = self.yolo_processor.add_info_overlay(
            annotated_frame, self.frame_count, 
            self.session_statistics['vehicle_counts'],
            self.session_statistics, self.speed_limit
        )
        
        # Add helmet annotations for motorcycles
        for detection in detections:
            if detection['vehicle_type'] == 'motorcycle':
                helmet_result = self.helmet_detector.detect_helmet_multi_method(frame, detection['bbox'])
                annotated_frame = self.helmet_detector.annotate_helmet_detection(
                    annotated_frame, detection['bbox'], helmet_result
                )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        self._update_processing_stats(processing_time)
        
        # Clean up old tracks to prevent memory buildup
        if self.frame_count % 100 == 0:
            self.speed_calculator.cleanup_old_tracks()
        
        return {
            'annotated_frame': annotated_frame,
            'detections': detections,
            'violations': frame_violations,
            'vehicle_counts': frame_vehicle_counts,
            'vehicle_speeds': vehicle_speeds,
            'frame_number': self.frame_count,
            'processing_time': processing_time,
            'timestamp': timestamp
        }
    
    def _create_speed_violation(self, detection: Dict, speed: float, 
                              frame_number: int, timestamp: str) -> Dict:
        """Create a speed violation record"""
        return {
            'type': 'OVERSPEEDING',
            'vehicle_type': detection['vehicle_type'],
            'speed': round(speed, 1),
            'speed_limit': self.speed_limit,
            'excess_speed': round(speed - self.speed_limit, 1),
            'confidence': detection['confidence'],
            'bbox': detection['bbox'],
            'frame_number': frame_number,
            'timestamp': timestamp,
            'details': {
                'detection_confidence': detection['confidence'],
                'vehicle_center': [detection['center_x'], detection['center_y']],
                'vehicle_size': [detection['width'], detection['height']]
            }
        }
    
    def _update_session_statistics(self, frame_counts: Dict, violations: List[Dict]):
        """Update session-wide statistics"""
        # Update vehicle counts
        for vehicle_type, count in frame_counts.items():
            self.session_statistics['vehicle_counts'][vehicle_type] += count
        
        # Update violation counts
        for violation in violations:
            self.session_violations.append(violation)
            self.session_statistics['total_violations'] += 1
            
            if violation['type'] == 'OVERSPEEDING':
                self.session_statistics['speed_violations'] += 1
            elif violation['type'] == 'NO_HELMET':
                self.session_statistics['helmet_violations'] += 1
            elif violation['type'] == 'RED_LIGHT_VIOLATION':
                self.session_statistics['red_light_violations'] += 1
    
    def _update_processing_stats(self, processing_time: float):
        """Update processing performance statistics"""
        stats = self.session_statistics['processing_stats']
        stats['frames_processed'] += 1
        stats['total_processing_time'] += processing_time
        stats['avg_processing_time'] = stats['total_processing_time'] / stats['frames_processed']
    
    def get_recent_violations(self, limit: int = 10) -> List[Dict]:
        """Get recent violations from current session"""
        return self.session_violations[-limit:] if self.session_violations else []
    
    def get_session_statistics(self) -> Dict:
        """Get current session statistics"""
        return self.session_statistics.copy()
    
    def set_speed_limit(self, speed_limit: float):
        """Update speed limit"""
        self.speed_limit = speed_limit
    
    def switch_model(self, model_name: str):
        """Switch YOLO model"""
        if model_name in self.yolo_processor.AVAILABLE_MODELS:
            self.model_name = model_name
            self.yolo_processor.switch_model(model_name)
        else:
            raise ValueError(f"Model {model_name} not available")
    
    def reset_session(self):
        """Reset session data for new detection session"""
        self.frame_count = 0
        self.session_violations = []
        self.session_statistics = {
            'total_violations': 0,
            'speed_violations': 0,
            'helmet_violations': 0,
            'red_light_violations': 0,
            'vehicle_counts': {
                'cars': 0,
                'bikes': 0,
                'buses': 0,
                'trucks': 0,
                'total': 0
            },
            'processing_stats': {
                'frames_processed': 0,
                'avg_processing_time': 0.0,
                'total_processing_time': 0.0
            }
        }
        self.speed_calculator.reset_tracking()
    
    def get_model_info(self) -> Dict:
        """Get information about current model and settings"""
        return {
            'model_name': self.model_name,
            'speed_limit': self.speed_limit,
            'available_models': list(self.yolo_processor.AVAILABLE_MODELS.keys()),
            'confidence_threshold': self.yolo_processor.confidence_threshold,
            'frame_count': self.frame_count
        }
    
    def set_confidence_threshold(self, threshold: float):
        """Set detection confidence threshold"""
        self.yolo_processor.set_confidence_threshold(threshold)
    
    def export_session_data(self) -> Dict:
        """Export complete session data for saving"""
        return {
            'session_info': {
                'model_name': self.model_name,
                'speed_limit': self.speed_limit,
                'frames_processed': self.frame_count,
                'start_time': datetime.now().isoformat(),  # This would be set at session start
                'end_time': datetime.now().isoformat()
            },
            'statistics': self.session_statistics,
            'violations': self.session_violations,
            'model_info': self.get_model_info()
        }