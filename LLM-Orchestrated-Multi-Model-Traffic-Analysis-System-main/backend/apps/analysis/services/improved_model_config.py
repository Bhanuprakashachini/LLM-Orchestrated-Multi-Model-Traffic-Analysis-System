"""
Improved Model Configuration for Accurate Vehicle Detection
Standardizes all YOLO models with optimal settings
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

class ImprovedModelConfig:
    """
    Standardized configuration for all YOLO models to ensure consistent detection
    """
    
    # STANDARDIZED DETECTION PARAMETERS
    CONFIDENCE_THRESHOLD = 0.25  # Balanced confidence for accuracy without false positives
    IOU_THRESHOLD = 0.45        # Standard IoU for proper NMS
    MAX_DETECTIONS = 300        # Reasonable limit for real scenarios
    AGNOSTIC_NMS = False        # Class-specific NMS for better accuracy
    
    # VEHICLE CLASS MAPPING (COCO dataset)
    VEHICLE_CLASSES = {
        1: 'bicycle',    # COCO class 1
        2: 'car',        # COCO class 2  
        3: 'motorcycle', # COCO class 3
        5: 'bus',        # COCO class 5
        7: 'truck'       # COCO class 7
    }
    
    # SIMPLIFIED OUTPUT CATEGORIES
    SIMPLIFIED_CATEGORIES = {
        'bicycle': '2-wheeler',
        'motorcycle': '2-wheeler', 
        'car': 'car',
        'bus': 'large_vehicle',
        'truck': 'large_vehicle'
    }
    
    # ROI FILTERING PARAMETERS
    ROI_HEIGHT_THRESHOLD = 0.25  # Use bottom 75% of image (road area)
    MIN_DETECTION_AREA = 400     # Minimum bounding box area
    MAX_DETECTION_AREA = 50000   # Maximum bounding box area
    MIN_WIDTH = 15               # Minimum bounding box width
    MIN_HEIGHT = 15              # Minimum bounding box height
    
    # TRACKING PARAMETERS
    TRACKING_MAX_DISTANCE = 150  # Maximum pixel distance for tracking
    TRACKING_MAX_DISAPPEARED = 30 # Maximum frames before deregistering
    
    @classmethod
    def get_vehicle_class_name(cls, class_id: int) -> Optional[str]:
        """Get vehicle class name from COCO class ID"""
        return cls.VEHICLE_CLASSES.get(class_id)
    
    @classmethod
    def get_simplified_category(cls, class_name: str) -> str:
        """Get simplified category for vehicle class"""
        return cls.SIMPLIFIED_CATEGORIES.get(class_name, 'unknown')
    
    @classmethod
    def is_valid_detection(cls, bbox: Tuple[float, float, float, float], 
                          image_shape: Tuple[int, int]) -> bool:
        """
        Validate detection based on size and position
        
        Args:
            bbox: (x1, y1, x2, y2) bounding box coordinates
            image_shape: (height, width) of image
            
        Returns:
            True if detection is valid, False otherwise
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        # Check minimum/maximum size constraints
        if (area < cls.MIN_DETECTION_AREA or 
            area > cls.MAX_DETECTION_AREA or
            width < cls.MIN_WIDTH or 
            height < cls.MIN_HEIGHT):
            return False
            
        # Check if detection is in road area (bottom 75% of image)
        image_height = image_shape[0]
        roi_top = image_height * cls.ROI_HEIGHT_THRESHOLD
        centroid_y = (y1 + y2) / 2
        
        return centroid_y > roi_top
    
    @classmethod
    def filter_detections(cls, detections: List[Dict], 
                         image_shape: Tuple[int, int]) -> List[Dict]:
        """
        Filter detections based on validation criteria
        
        Args:
            detections: List of detection dictionaries
            image_shape: (height, width) of image
            
        Returns:
            Filtered list of valid detections
        """
        valid_detections = []
        
        for detection in detections:
            bbox = detection.get('bbox', [0, 0, 0, 0])
            class_id = detection.get('class_id', -1)
            confidence = detection.get('confidence', 0.0)
            
            # Check if it's a vehicle class
            if class_id not in cls.VEHICLE_CLASSES:
                continue
                
            # Check confidence threshold
            if confidence < cls.CONFIDENCE_THRESHOLD:
                continue
                
            # Check detection validity
            if not cls.is_valid_detection(bbox, image_shape):
                continue
                
            # Add simplified category
            class_name = cls.get_vehicle_class_name(class_id)
            detection['class_name'] = class_name
            detection['category'] = cls.get_simplified_category(class_name)
            
            valid_detections.append(detection)
        
        return valid_detections
    
    @classmethod
    def apply_nms(cls, detections: List[Dict]) -> List[Dict]:
        """
        Apply Non-Maximum Suppression to remove overlapping detections
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            List of detections after NMS
        """
        if not detections:
            return []
        
        # Convert to numpy arrays for NMS
        boxes = np.array([det['bbox'] for det in detections])
        scores = np.array([det['confidence'] for det in detections])
        
        # Simple NMS implementation
        indices = []
        sorted_indices = np.argsort(scores)[::-1]
        
        while len(sorted_indices) > 0:
            current = sorted_indices[0]
            indices.append(current)
            
            if len(sorted_indices) == 1:
                break
                
            # Calculate IoU with remaining boxes
            current_box = boxes[current]
            remaining_boxes = boxes[sorted_indices[1:]]
            
            ious = cls._calculate_iou(current_box, remaining_boxes)
            
            # Keep boxes with IoU less than threshold
            keep_indices = np.where(ious < cls.IOU_THRESHOLD)[0]
            sorted_indices = sorted_indices[keep_indices + 1]
        
        return [detections[i] for i in indices]
    
    @classmethod
    def _calculate_iou(cls, box1: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Calculate IoU between one box and multiple boxes"""
        x1_max = np.maximum(box1[0], boxes[:, 0])
        y1_max = np.maximum(box1[1], boxes[:, 1])
        x2_min = np.minimum(box1[2], boxes[:, 2])
        y2_min = np.minimum(box1[3], boxes[:, 3])
        
        intersection_area = np.maximum(0, x2_min - x1_max) * np.maximum(0, y2_min - y1_max)
        
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        
        union_area = box1_area + boxes_area - intersection_area
        
        return intersection_area / np.maximum(union_area, 1e-6)

    @classmethod
    def get_model_summary(cls) -> Dict:
        """Get summary of model configuration"""
        return {
            'confidence_threshold': cls.CONFIDENCE_THRESHOLD,
            'iou_threshold': cls.IOU_THRESHOLD,
            'max_detections': cls.MAX_DETECTIONS,
            'vehicle_classes': list(cls.VEHICLE_CLASSES.values()),
            'simplified_categories': list(set(cls.SIMPLIFIED_CATEGORIES.values())),
            'roi_height_threshold': cls.ROI_HEIGHT_THRESHOLD,
            'tracking_max_distance': cls.TRACKING_MAX_DISTANCE,
            'tracking_max_disappeared': cls.TRACKING_MAX_DISAPPEARED
        }