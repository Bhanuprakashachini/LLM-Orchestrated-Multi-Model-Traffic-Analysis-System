"""
Improved YOLOv12 Traffic Analysis Service - FIXED VERSION
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ImprovedYOLOv12Analyzer:
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.25):
        self.model_path = model_path or self._get_best_model_path()
        self.model = None
        self.base_confidence_threshold = confidence_threshold  # Store base threshold
        self.confidence_threshold = confidence_threshold
        
        # FIXED: Proper vehicle class mapping (COCO dataset)
        self.vehicle_classes = {
            2: 'car',        # COCO class 2
            3: 'motorcycle', # COCO class 3  
            5: 'bus',        # COCO class 5
            7: 'truck',      # COCO class 7
            1: 'bicycle'     # COCO class 1
        }
        
        # FIXED: Ultra-sensitive detection parameters for maximum detection
        self.iou_threshold = 0.2  # Very low IoU for dense traffic
        self.max_detections = 2000  # Much higher limit
        self.agnostic_nms = True  # Better for mixed vehicle types
        
        # Load model
        self._load_model()
        
        logger.info(f"Improved YOLOv12 analyzer initialized")
    
    def _get_best_model_path(self) -> str:
        """Get the best available YOLOv12 model - centralized to backend/models/"""
        # Use centralized models directory
        centralized_path = Path(__file__).parent.parent.parent / 'models' / 'yolo12s.pt'
        if centralized_path.exists():
            return str(centralized_path)
        
        # Fallback to download
        return 'yolo12s.pt'
    
    def _load_model(self):
        """Load YOLOv12 model with error handling"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info(f"Successfully loaded YOLOv12 model: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLOv12 model: {e}")
            raise
    
    def detect_vehicles(self, image: np.ndarray) -> List[Dict]:
        """Detect vehicles in image with improved accuracy"""
        if self.model is None:
            logger.error("Model not loaded")
            return []
        
        try:
            # Run inference with optimized parameters
            results = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                max_det=self.max_detections,
                agnostic_nms=self.agnostic_nms,
                verbose=False
            )
            
            detections = []
            
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes
                    
                    for i in range(len(boxes)):
                        # Extract detection data
                        box = boxes.xyxy[i].cpu().numpy()
                        confidence = float(boxes.conf[i].cpu().numpy())
                        class_id = int(boxes.cls[i].cpu().numpy())
                        
                        # FIXED: Only process vehicle classes
                        if class_id not in self.vehicle_classes:
                            continue
                        
                        x1, y1, x2, y2 = box
                        
                        # FIXED: Validate detection size and position
                        if not self._is_valid_detection(x1, y1, x2, y2, image.shape):
                            continue
                        
                        detection = {
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': self.vehicle_classes[class_id],
                            'centroid': [(x1 + x2) / 2, (y1 + y2) / 2]
                        }
                        
                        detections.append(detection)
            
            # FIXED: Apply additional filtering
            detections = self._filter_detections(detections, image.shape)
            
            logger.info(f"YOLOv12 detected {len(detections)} vehicles")
            return detections
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def _is_valid_detection(self, x1: float, y1: float, x2: float, y2: float, 
                           image_shape: Tuple[int, int, int]) -> bool:
        """Validate detection based on size and position"""
        height, width = image_shape[:2]
        
        # Calculate detection properties
        det_width = x2 - x1
        det_height = y2 - y1
        det_area = det_width * det_height
        centroid_y = (y1 + y2) / 2
        
        # FIXED: Very lenient size filtering for distant vehicles
        if det_width < 5 or det_height < 4:  # Even smaller minimum size
            return False
        if det_area < 25:  # Much smaller minimum area (5x5 pixels)
            return False
        if det_area > height * width * 0.5:  # Only filter extremely large detections
            return False
        
        # FIXED: Include more of the image - only exclude very top
        road_threshold = height * 0.1  # Only exclude top 10% instead of 20%
        if centroid_y < road_threshold:
            return False
        
        # Check bounds
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
            return False
        
        return True

    def _analyze_image_conditions(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image conditions to determine appropriate filtering strategy"""
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Basic image statistics
            contrast = np.std(gray)
            brightness = np.mean(gray)
            
            # Analyze potential vehicle density using edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (image.shape[0] * image.shape[1])
            
            # Analyze histogram for various conditions
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            dark_pixels_ratio = np.sum(hist[:80]) / np.sum(hist)  # Pixels with intensity < 80
            bright_pixels_ratio = np.sum(hist[200:]) / np.sum(hist)  # Pixels with intensity > 200
            mid_pixels_ratio = np.sum(hist[80:200]) / np.sum(hist)  # Mid-range pixels
            
            # Color analysis for weather detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            saturation_mean = np.mean(s)
            saturation_std = np.std(s)
            
            # Texture analysis for rain/snow detection
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Advanced condition detection
            visibility = self._detect_weather_conditions(
                brightness, contrast, dark_pixels_ratio, bright_pixels_ratio,
                saturation_mean, saturation_std, laplacian_var
            )
            
            # Estimate density hint
            if edge_density > 0.15:
                density_hint = 'very_dense'
            elif edge_density > 0.10:
                density_hint = 'dense'
            elif edge_density > 0.05:
                density_hint = 'moderate'
            else:
                density_hint = 'light'
            
            return {
                'visibility': visibility,
                'density_hint': density_hint,
                'contrast': contrast,
                'brightness': brightness,
                'edge_density': edge_density,
                'dark_pixels_ratio': dark_pixels_ratio,
                'bright_pixels_ratio': bright_pixels_ratio,
                'saturation_mean': saturation_mean,
                'saturation_std': saturation_std,
                'laplacian_var': laplacian_var
            }
            
        except Exception as e:
            logger.error(f"Image condition analysis failed: {e}")
            return {'visibility': 'good', 'density_hint': 'moderate'}
    
    def _detect_weather_conditions(self, brightness: float, contrast: float, 
                                 dark_ratio: float, bright_ratio: float,
                                 sat_mean: float, sat_std: float, texture_var: float) -> str:
        """Detect specific weather and lighting conditions"""
        
        # Night detection
        if brightness < 60 and dark_ratio > 0.6:
            return 'night'
        
        # Very dark/twilight conditions
        elif brightness < 80 and dark_ratio > 0.5:
            return 'twilight'
        
        # Fog detection (low contrast, high brightness, low saturation)
        elif contrast < 30 and brightness > 120 and sat_mean < 50:
            return 'dense_fog'
        elif contrast < 40 and brightness > 100 and sat_mean < 60:
            return 'light_fog'
        
        # Rain detection (low contrast, reduced saturation, specific texture patterns)
        elif contrast < 45 and sat_mean < 70 and texture_var > 100 and brightness < 120:
            return 'heavy_rain'
        elif contrast < 55 and sat_mean < 80 and texture_var > 80:
            return 'light_rain'
        
        # Snow detection (high brightness, low saturation, high bright pixel ratio)
        elif brightness > 140 and bright_ratio > 0.3 and sat_mean < 40:
            return 'snow'
        elif brightness > 120 and bright_ratio > 0.2 and sat_mean < 50:
            return 'light_snow'
        
        # Overcast conditions (low contrast, medium brightness, low saturation)
        elif contrast < 50 and 90 < brightness < 130 and sat_mean < 70:
            return 'overcast'
        
        # Glare/bright sun conditions (very high brightness, high bright pixel ratio)
        elif brightness > 160 and bright_ratio > 0.4:
            return 'bright_glare'
        elif brightness > 140 and bright_ratio > 0.25:
            return 'sunny_glare'
        
        # Haze conditions (medium contrast, high brightness, medium saturation)
        elif 40 < contrast < 60 and brightness > 110 and 60 < sat_mean < 90:
            return 'haze'
        
        # Dust/sandstorm (low contrast, medium-high brightness, very low saturation)
        elif contrast < 35 and brightness > 100 and sat_mean < 30:
            return 'dust'
        
        # Poor general visibility
        elif contrast < 50:
            return 'poor'
        
        # Excellent conditions
        elif contrast > 80 and sat_mean > 80:
            return 'excellent'
        
        # Good conditions (default)
        else:
            return 'good'
    
    def _get_adaptive_confidence_threshold(self, conditions: Dict[str, Any], vehicle_type: str) -> float:
        """Get adaptive confidence threshold based on image conditions"""
        
        # Base thresholds
        base_thresholds = {
            'car': self.base_confidence_threshold,
            'truck': self.base_confidence_threshold * 0.8,
            'bus': self.base_confidence_threshold * 0.8,
            'motorcycle': self.base_confidence_threshold * 0.6,
            'bicycle': self.base_confidence_threshold * 0.6
        }
        
        base_threshold = base_thresholds.get(vehicle_type, self.base_confidence_threshold)
        
        # Adjust based on visibility/weather conditions
        visibility = conditions.get('visibility', 'good')
        
        # Weather-specific adjustments
        weather_adjustments = {
            # Very challenging conditions - major threshold reduction
            'night': -0.18,
            'dense_fog': -0.16,
            'heavy_rain': -0.15,
            'snow': -0.14,
            'dust': -0.13,
            
            # Moderately challenging conditions
            'twilight': -0.12,
            'light_fog': -0.10,
            'light_rain': -0.08,
            'light_snow': -0.08,
            'overcast': -0.06,
            'haze': -0.05,
            
            # Bright conditions that can cause issues
            'bright_glare': -0.10,  # Glare can hide vehicles
            'sunny_glare': -0.05,
            
            # Poor general conditions
            'poor': -0.08,
            
            # Good conditions
            'good': 0.0,
            'excellent': 0.02  # Can afford slightly higher threshold
        }
        
        visibility_adjustment = weather_adjustments.get(visibility, 0.0)
        
        # Adjust based on density hint
        density = conditions.get('density_hint', 'moderate')
        if density == 'very_dense':
            # Lower threshold for dense traffic to catch more vehicles
            density_adjustment = -0.10
        elif density == 'dense':
            density_adjustment = -0.05
        elif density == 'light':
            # Slightly higher threshold for light traffic to reduce false positives
            density_adjustment = 0.03
        else:
            density_adjustment = 0.0
        
        # Calculate final threshold
        final_threshold = base_threshold + visibility_adjustment + density_adjustment
        
        # Ensure reasonable bounds - but respect ultra-low thresholds for dense traffic
        final_threshold = max(original_threshold, min(0.40, final_threshold))
        
        return final_threshold
        return True
    
    def _filter_detections(self, detections: List[Dict], 
                          image_shape: Tuple[int, int, int]) -> List[Dict]:
        """Apply additional filtering to remove false positives"""
        if not detections:
            return []
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Apply confidence-based filtering with adaptive thresholds
        filtered_by_confidence = []
        for detection in detections:
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Use the analyzer's confidence threshold instead of hardcoded values
            # This allows for ultra-low thresholds when needed for dense traffic
            min_confidence = self.confidence_threshold
            
            if confidence >= min_confidence:
                filtered_by_confidence.append(detection)
        
        # Apply aspect ratio filtering
        filtered_by_ratio = []
        for detection in filtered_by_confidence:
            bbox = detection['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            aspect_ratio = width / height if height > 0 else 0
            
            # Vehicle aspect ratios should be reasonable
            # Cars: typically 1.5-3.0, Trucks: 2.0-4.0, Motorcycles: 0.8-2.0
            if 0.3 <= aspect_ratio <= 5.0:  # Very lenient range
                filtered_by_ratio.append(detection)
        
        # Apply position-based filtering
        height, width = image_shape[:2]
        filtered_by_position = []
        
        for detection in filtered_by_ratio:
            bbox = detection['bbox']
            centroid_x = (bbox[0] + bbox[2]) / 2
            centroid_y = (bbox[1] + bbox[3]) / 2
            
            # Vehicles should be in reasonable positions
            # Exclude extreme edges and very top of image
            margin_x = width * 0.02  # 2% margin from sides
            margin_y_top = height * 0.15  # 15% margin from top
            margin_y_bottom = height * 0.02  # 2% margin from bottom
            
            if (margin_x <= centroid_x <= width - margin_x and 
                margin_y_top <= centroid_y <= height - margin_y_bottom):
                filtered_by_position.append(detection)
        
        # Remove overlapping detections (improved NMS)
        filtered = []
        for detection in filtered_by_position:
            is_duplicate = False
            
            for existing in filtered:
                iou = self._calculate_iou(detection['bbox'], existing['bbox'])
                
                # Different IoU thresholds based on vehicle types
                same_class = detection['class_name'] == existing['class_name']
                iou_threshold = 0.4 if same_class else 0.3
                
                if iou > iou_threshold:
                    # Keep the one with higher confidence
                    if detection['confidence'] > existing['confidence']:
                        filtered.remove(existing)
                        filtered.append(detection)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(detection)
        
        # Final sanity check - limit maximum detections to prevent extreme false positives
        max_vehicles = min(200, len(filtered))  # Cap at 200 vehicles max
        filtered = filtered[:max_vehicles]
        
        logger.info(f"YOLOv12 Filtering: {len(detections)} -> {len(filtered)} vehicles (removed {len(detections) - len(filtered)} false positives)")
        
        return filtered
    
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union (IoU) between two boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze single image and return comprehensive results"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            start_time = time.time()
            
            # Analyze image conditions for adaptive filtering
            conditions = self._analyze_image_conditions(image)
            
            # Adjust confidence threshold based on conditions
            original_threshold = self.confidence_threshold
            
            # For challenging weather/lighting conditions, use lower threshold
            challenging_conditions = [
                'night', 'twilight', 'dense_fog', 'light_fog', 'heavy_rain', 'light_rain',
                'snow', 'light_snow', 'overcast', 'haze', 'dust', 'bright_glare', 'sunny_glare'
            ]
            
            if (conditions['visibility'] in challenging_conditions or 
                conditions['density_hint'] in ['very_dense', 'dense']):
                
                # More aggressive threshold reduction for very challenging conditions
                very_challenging = ['night', 'dense_fog', 'heavy_rain', 'snow', 'dust']
                if conditions['visibility'] in very_challenging:
                    self.confidence_threshold = max(original_threshold, original_threshold * 0.4)  # Don't go below original
                else:
                    self.confidence_threshold = max(original_threshold, original_threshold * 0.5)  # Don't go below original
                
                logger.info(f"YOLOv12 Adaptive threshold: {original_threshold:.2f} -> {self.confidence_threshold:.2f} (conditions: {conditions['visibility']}, {conditions['density_hint']})")
            
            # Detect vehicles
            detections = self.detect_vehicles(image)
            
            # Restore original threshold
            self.confidence_threshold = original_threshold
            
            processing_time = time.time() - start_time
            
            # Count vehicles by type
            vehicle_counts = {}
            for detection in detections:
                class_name = detection['class_name']
                vehicle_counts[class_name] = vehicle_counts.get(class_name, 0) + 1
            
            # Create the expected vehicle_breakdown structure for comprehensive service compatibility
            vehicle_breakdown = {
                'by_type': {}
            }
            
            # Convert vehicle_counts to the expected format
            for vehicle_type, count in vehicle_counts.items():
                vehicle_breakdown['by_type'][vehicle_type] = {
                    'count': count,
                    'avg_confidence': np.mean([d['confidence'] for d in detections if d['class_name'] == vehicle_type]) if any(d['class_name'] == vehicle_type for d in detections) else 0.0
                }
            
            # Group vehicle counts into the expected categories for backward compatibility
            grouped_vehicle_counts = {
                'cars': vehicle_counts.get('car', 0),
                'large_vehicles': vehicle_counts.get('truck', 0) + vehicle_counts.get('bus', 0),
                '2_wheelers': vehicle_counts.get('motorcycle', 0) + vehicle_counts.get('bicycle', 0)
            }
            
            logger.info(f"🚗 YOLOv12 vehicle breakdown: Raw={vehicle_counts}, Grouped={grouped_vehicle_counts}")
            logger.info(f"📊 Vehicle breakdown structure: {vehicle_breakdown}")
            
            # Calculate metrics
            total_vehicles = len(detections)
            avg_confidence = np.mean([d['confidence'] for d in detections]) if detections else 0.0
            
            results = {
                'model_name': 'YOLOv12_Improved',
                'image_path': image_path,
                'total_vehicles': total_vehicles,
                'vehicle_counts': grouped_vehicle_counts,  # Use grouped counts (for backward compatibility)
                'vehicle_breakdown': vehicle_breakdown,  # Add proper structure for comprehensive service
                'raw_vehicle_counts': vehicle_counts,  # Keep raw counts for debugging
                'detections': detections,
                'processing_time': processing_time,
                'average_confidence': float(avg_confidence),
                'image_shape': image.shape,
                'image_conditions': conditions,  # Include condition analysis
                'success': True
            }
            
            logger.info(f"YOLOv12 analysis complete: {total_vehicles} vehicles detected (conditions: {conditions['visibility']}, {conditions['density_hint']})")
            return results
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                'model_name': 'YOLOv12_Improved',
                'image_path': image_path,
                'success': False,
                'error': str(e)
            }
    
    def create_annotated_image(self, image_path: str, output_path: str) -> bool:
        """Create annotated image with detection results"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            # Get detections
            detections = self.detect_vehicles(image)
            
            # Draw annotations
            annotated_image = image.copy()
            
            for detection in detections:
                x1, y1, x2, y2 = [int(coord) for coord in detection['bbox']]
                confidence = detection['confidence']
                class_name = detection['class_name']
                
                # Choose color based on grouped vehicle type
                colors = {
                    'car': (0, 255, 0),           # Bright Green for Cars
                    'truck': (255, 0, 0),         # Bright Red for Large Vehicles
                    'bus': (255, 0, 0),           # Bright Red for Large Vehicles
                    'motorcycle': (0, 0, 255),    # Bright Blue for 2-Wheelers
                    'bicycle': (0, 0, 255),       # Bright Blue for 2-Wheelers (same as motorcycle)
                    'large_vehicle': (255, 0, 0), # Bright Red for Large Vehicles
                    '2-wheeler': (0, 0, 255),     # Bright Blue for 2-Wheelers
                }
                color = colors.get(class_name, (128, 128, 128))
                
                # Draw bounding box
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
                
                # Map individual classes to grouped categories for display
                class_display_mapping = {
                    'car': 'Car',
                    'truck': 'Large Vehicle',
                    'bus': 'Large Vehicle', 
                    'motorcycle': '2-Wheeler',
                    'bicycle': '2-Wheeler',
                    'large_vehicle': 'Large Vehicle',
                    '2-wheeler': '2-Wheeler'
                }
                
                # Use grouped class name for label
                display_class = class_display_mapping.get(class_name, class_name.replace('_', ' ').title())
                
                # Draw label with grouped category
                label = f"v12i-{display_class}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                
                # Background for label
                cv2.rectangle(annotated_image, 
                            (x1, y1 - label_size[1] - 10),
                            (x1 + label_size[0], y1),
                            color, -1)
                
                # Label text
                cv2.putText(annotated_image, label,
                          (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                          (255, 255, 255), 2)
            
            # Add summary text
            total_vehicles = len(detections)
            summary = f"YOLOv12 Improved: {total_vehicles} vehicles detected"
            cv2.putText(annotated_image, summary,
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                       (0, 255, 255), 2)
            
            # Save annotated image
            success = cv2.imwrite(output_path, annotated_image)
            
            if success:
                logger.info(f"Annotated image saved: {output_path}")
            else:
                logger.error(f"Failed to save annotated image: {output_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Annotation failed: {e}")
            return False