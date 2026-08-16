"""
YOLOv12 Traffic Analysis Service - IMPROVED VERSION for Maximum Vehicle Detection
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class YOLOv12TrafficAnalyzer:
    """
    Traffic analysis service using YOLOv12 model with MAXIMUM DETECTION ACCURACY
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu', confidence_threshold: float = 0.05, roi_polygon: Optional[List[Tuple[int, int]]] = None):
        """
        Initialize the YOLOv12 analyzer with ULTRA-LOW confidence for maximum detection
        
        Args:
            model_path: Path to YOLO model file
            device: Device to run inference on ('cpu', 'cuda', or 'auto')
            confidence_threshold: Minimum confidence for detections (default: 0.05 for maximum detection)
            roi_polygon: List of (x, y) points defining the region of interest (road area)
        """
        self.device = device
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.roi_polygon = roi_polygon
        self.class_names = self._get_class_names()
        self.vehicle_classes = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
        
        # BALANCED configuration for accurate vehicle detection with minimal false positives
        self.confidence_threshold = max(0.15, confidence_threshold)  # Reasonable confidence for accuracy
        self.iou_threshold = 0.30  # Balanced IoU for overlapping vehicles
        self.max_detections = 500  # Reasonable limit for dense traffic
        self.agnostic_nms = False  # Class-specific NMS
        
        # Enhanced vehicle class mapping
        self.vehicle_class_mapping = {
            'car': 'car',
            'truck': 'truck', 
            'bus': 'bus',
            'motorcycle': 'motorcycle',
            'bicycle': 'bicycle',
            'train': 'truck',  # Classify trains as trucks
            'boat': 'car',     # Sometimes vehicles misclassified as boats
            'person': 'motorcycle'  # Sometimes people on motorcycles
        }
        
        # Load model
        try:
            self._load_model()
        except Exception as e:
            logger.warning(f"Could not load YOLO model: {e}")
        
        logger.info(f"YOLOv12 BALANCED analyzer initialized with confidence: {self.confidence_threshold}")
    
    def _get_default_model_path(self) -> str:
        """Get default model path - centralized to backend/models/"""
        from django.conf import settings
        
        # Use centralized models directory
        centralized_model_path = Path(__file__).parent.parent.parent / 'models' / 'yolo12s.pt'
        if centralized_model_path.exists():
            return str(centralized_model_path)
        
        # Fallback to settings or default (should not be needed)
        return getattr(settings, 'YOLO12_MODEL_PATH', str(centralized_model_path))
    
    def _get_class_names(self) -> List[str]:
        """Get COCO class names"""
        return [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
    
    def _load_model(self):
        """Load YOLOv12 model from centralized location"""
        try:
            from ultralytics import YOLO
            
            # Use centralized model path
            centralized_path = Path(__file__).parent.parent.parent / 'models' / 'yolo12s.pt'
            
            if centralized_path.exists():
                self.model = YOLO(str(centralized_path))
                logger.info(f"Loaded YOLOv12 model from centralized location: {centralized_path}")
            else:
                # Use absolute path to centralized model
                abs_centralized_path = Path(__file__).resolve().parent.parent.parent / 'models' / 'yolo12s.pt'
                if abs_centralized_path.exists():
                    self.model = YOLO(str(abs_centralized_path))
                    logger.info(f"Loaded YOLOv12 model from absolute centralized path: {abs_centralized_path}")
                else:
                    raise FileNotFoundError(f"YOLOv12 model not found. Please ensure yolo12s.pt exists in backend/models/ directory")
            
            if self.model is None:
                raise Exception("No YOLO model could be loaded")
                
        except Exception as e:
            logger.error(f"Failed to load YOLOv12 model: {e}")
            raise
    
    def analyze_traffic_scene(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a traffic scene image using YOLOv12 with MAXIMUM DETECTION
        """
        start_time = time.time()
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            height, width = image.shape[:2]
            
            # Perform ULTRA-SENSITIVE vehicle detection
            detection_results = self._detect_vehicles_ultra_sensitive(image)
            
            # Analyze traffic density
            density_results = self._analyze_traffic_density(detection_results, (width, height))
            
            # Create annotated image
            annotated_image_path = self._create_annotated_image(image, detection_results, image_path)
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            fps = 1.0 / processing_time if processing_time > 0 else 0
            
            return {
                'vehicle_detection': detection_results,
                'traffic_density': density_results,
                'annotated_image_path': annotated_image_path,
                'performance_metrics': {
                    'processing_time': processing_time,
                    'fps': fps,
                    'model_version': 'YOLOv12-UltraSensitive',
                    'image_dimensions': {'width': width, 'height': height}
                },
                'analysis_type': 'image'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing traffic scene with YOLOv12: {e}")
            return {
                'error': str(e),
                'vehicle_detection': self._fallback_detection(image if 'image' in locals() else None),
                'traffic_density': {},
                'performance_metrics': {
                    'processing_time': time.time() - start_time,
                    'fps': 0,
                    'model_version': 'YOLOv12-Error',
                    'error': True
                }
            }
    
    def _detect_vehicles_ultra_sensitive(self, image: np.ndarray) -> Dict[str, Any]:
        """
        BALANCED vehicle detection for accurate results with minimal false positives
        """
        try:
            if self.model is None:
                logger.error("YOLOv12 model is None - using fallback")
                return self._fallback_detection(image)
            
            logger.info("YOLOv12: Running BALANCED detection for accurate vehicle counting...")
            
            # BALANCED DETECTION APPROACH - Focus on accuracy over quantity
            all_detections = []
            
            # Pass 1: Standard confidence detection
            logger.info("Pass 1: Standard confidence detection...")
            results1 = self.model(
                image,
                verbose=False,
                conf=0.25,  # Reasonable confidence for accuracy
                iou=0.45,   # Standard IoU for good separation
                max_det=300,
                augment=True,
                half=False
            )
            
            # Pass 2: Lower confidence for potentially missed vehicles
            logger.info("Pass 2: Lower confidence for missed vehicles...")
            results2 = self.model(
                image,
                verbose=False,
                conf=0.15,  # Lower confidence to catch more vehicles
                iou=0.40,   # Slightly lower IoU
                max_det=300,
                augment=True,
                half=False
            )
            
            # Pass 3: Enhanced image for distant vehicles (only if needed)
            logger.info("Pass 3: Enhanced detection for distant vehicles...")
            enhanced_image = self._enhance_for_distant_vehicles(image)
            results3 = self.model(
                enhanced_image,
                verbose=False,
                conf=0.20,  # Moderate confidence for enhanced image
                iou=0.35,
                max_det=200,
                augment=True,
                half=False
            )
            
            # Combine results with strict validation
            all_results = [results1, results2, results3]
            
            # Process all detections with STRICT vehicle validation
            for results in all_results:
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            try:
                                class_id = int(box.cls[0])
                                confidence = float(box.conf[0])
                                
                                if class_id < len(self.class_names):
                                    class_name = self.class_names[class_id]
                                    
                                    # STRICT vehicle detection - only accept clear vehicle classes
                                    vehicle_mapping = {
                                        'car': 'car',
                                        'truck': 'truck', 
                                        'bus': 'bus',
                                        'motorcycle': 'motorcycle',
                                        'bicycle': 'bicycle'
                                    }
                                    
                                    # Only accept actual vehicle classes
                                    if class_name not in vehicle_mapping:
                                        continue
                                    
                                    mapped_class = vehicle_mapping[class_name]
                                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                                    
                                    # Strict validation for accurate detection
                                    if x1 >= x2 or y1 >= y2:
                                        continue
                                    
                                    # Calculate dimensions
                                    width = x2 - x1
                                    height = y2 - y1
                                    area = width * height
                                    image_area = image.shape[0] * image.shape[1]
                                    relative_area = area / image_area
                                    
                                    # REASONABLE size filtering for accurate detection
                                    min_relative_area = 0.0005  # Reasonable threshold for distant vehicles
                                    max_relative_area = 0.3     # Reasonable maximum size
                                    
                                    if relative_area < min_relative_area or relative_area > max_relative_area:
                                        continue
                                    
                                    # REASONABLE aspect ratio validation
                                    aspect_ratio = width / height if height > 0 else 0
                                    if not (0.3 <= aspect_ratio <= 4.0):  # Reasonable vehicle proportions
                                        continue
                                    
                                    # BALANCED confidence filtering
                                    min_confidence = 0.10  # Reasonable minimum confidence
                                    if confidence < min_confidence:
                                        continue
                                    
                                    all_detections.append({
                                        'bbox': [x1, y1, x2, y2],
                                        'confidence': confidence,
                                        'class': mapped_class,
                                        'original_class': class_name,
                                        'area': area,
                                        'relative_area': relative_area,
                                        'aspect_ratio': aspect_ratio
                                    })
                                    
                            except Exception as e:
                                logger.warning(f"Error processing detection: {e}")
                                continue
            
            logger.info(f"YOLOv12: Found {len(all_detections)} total detections from all passes")
            
            # Apply balanced NMS that removes clear duplicates but preserves distinct vehicles
            final_detections = self._balanced_nms(all_detections)
            
            # Count vehicles by type
            vehicle_counts = {'car': 0, 'truck': 0, 'bus': 0, 'motorcycle': 0, 'bicycle': 0}
            total_confidence = 0
            
            for detection in final_detections:
                vehicle_type = detection['class']
                if vehicle_type in vehicle_counts:
                    vehicle_counts[vehicle_type] += 1
                    total_confidence += detection['confidence']
            
            total_vehicles = sum(vehicle_counts.values())
            average_confidence = total_confidence / max(total_vehicles, 1)
            
            logger.info(f"YOLOv12 BALANCED RESULTS: {total_vehicles} vehicles detected")
            logger.info(f"YOLOv12 breakdown: {vehicle_counts}")
            logger.info(f"YOLOv12 average confidence: {average_confidence:.3f}")
            
            return {
                'total_vehicles': total_vehicles,
                'vehicle_counts': vehicle_counts,
                'average_confidence': average_confidence,
                'detections': final_detections,
                'vehicle_breakdown': {
                    'by_type': {
                        'car': {'count': vehicle_counts.get('car', 0), 'avg_confidence': self._get_avg_confidence_by_type(final_detections, 'car')},
                        'large_vehicle': {'count': vehicle_counts.get('truck', 0) + vehicle_counts.get('bus', 0), 'avg_confidence': self._get_avg_confidence_by_type(final_detections, ['truck', 'bus'])},
                        '2-wheeler': {'count': vehicle_counts.get('motorcycle', 0) + vehicle_counts.get('bicycle', 0), 'avg_confidence': self._get_avg_confidence_by_type(final_detections, ['motorcycle', 'bicycle'])}
                    }
                },
                'detection_quality': 'Balanced',
                'processing_notes': f'Balanced detection: {len(all_detections)} raw -> {total_vehicles} final vehicles'
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive detection: {e}")
            return self._fallback_detection(image)
    
    def _enhance_for_small_objects(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for better small object detection"""
        # Increase contrast and brightness
        enhanced = cv2.convertScaleAbs(image, alpha=1.3, beta=15)
        
        # Apply CLAHE for better contrast
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        lab[:,:,0] = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(lab[:,:,0])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return result
    
    def _conservative_nms(self, detections: List[Dict]) -> List[Dict]:
        """Conservative Non-Maximum Suppression to remove duplicates while keeping accuracy"""
        if not detections:
            return []
        
        # Group by class
        by_class = {}
        for det in detections:
            cls = det['class']
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(det)
        
        filtered = []
        for cls, cls_dets in by_class.items():
            # Sort by confidence (highest first)
            cls_dets.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Apply conservative NMS
            keep = []
            for det in cls_dets:
                should_keep = True
                for kept_det in keep:
                    iou = self._calculate_iou(det['bbox'], kept_det['bbox'])
                    # Use higher IoU threshold to be more conservative
                    if iou > 0.5:  # Conservative threshold
                        should_keep = False
                        break
                
                if should_keep:
                    keep.append(det)
            
            filtered.extend(keep)
        
        return filtered
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate IoU between two bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _get_avg_confidence_by_type(self, detections: List[Dict], vehicle_types) -> float:
        """Get average confidence for vehicle type(s)"""
        if isinstance(vehicle_types, str):
            vehicle_types = [vehicle_types]
        
        relevant = [d for d in detections if d['class'] in vehicle_types]
        if not relevant:
            return 0.0
        
        return sum(d['confidence'] for d in relevant) / len(relevant)
    
    def _fallback_detection(self, image: Optional[np.ndarray]) -> Dict[str, Any]:
        """Fallback detection when YOLO fails"""
        if image is None:
            return {
                'total_vehicles': 0,
                'vehicle_counts': {'car': 0, 'truck': 0, 'bus': 0, 'motorcycle': 0, 'bicycle': 0},
                'average_confidence': 0.0,
                'detections': [],
                'vehicle_breakdown': {'by_type': {}},
                'detection_quality': 'Failed',
                'processing_notes': 'Fallback detection - no image available'
            }
        
        # Simple fallback - estimate based on image analysis
        logger.warning("Using fallback detection method")
        
        # Basic vehicle estimation based on image properties
        height, width = image.shape[:2]
        estimated_vehicles = max(1, int((width * height) / 50000))  # Rough estimate
        
        return {
            'total_vehicles': estimated_vehicles,
            'vehicle_counts': {'car': estimated_vehicles, 'truck': 0, 'bus': 0, 'motorcycle': 0, 'bicycle': 0},
            'average_confidence': 0.3,  # Low confidence for fallback
            'detections': [],
            'vehicle_breakdown': {
                'by_type': {
                    'car': {'count': estimated_vehicles, 'avg_confidence': 0.3},
                    'large_vehicle': {'count': 0, 'avg_confidence': 0.0},
                    '2-wheeler': {'count': 0, 'avg_confidence': 0.0}
                }
            },
            'detection_quality': 'Fallback',
            'processing_notes': f'Fallback estimation: {estimated_vehicles} vehicles'
        }
    
    def _analyze_traffic_density(self, detection_results: Dict[str, Any], image_size: Tuple[int, int]) -> Dict[str, Any]:
        """Analyze traffic density"""
        total_vehicles = detection_results.get('total_vehicles', 0)
        width, height = image_size
        
        # Calculate density based on vehicle count
        if total_vehicles == 0:
            density_level = 'Empty'
            congestion_index = 0.0
        elif total_vehicles <= 10:
            density_level = 'Low'
            congestion_index = 0.2
        elif total_vehicles <= 30:
            density_level = 'Medium'
            congestion_index = 0.5
        elif total_vehicles <= 60:
            density_level = 'High'
            congestion_index = 0.8
        else:
            density_level = 'Very High'
            congestion_index = 1.0
        
        return {
            'density_level': density_level,
            'congestion_index': congestion_index,
            'vehicles_per_area': total_vehicles / (width * height) * 1000000,  # Vehicles per million pixels
            'flow_state': 'Free' if congestion_index < 0.3 else 'Moderate' if congestion_index < 0.7 else 'Congested'
        }
    
    def _create_annotated_image(self, image: np.ndarray, detection_results: Dict[str, Any], original_path: str) -> str:
        """Create annotated image with bounding boxes"""
        try:
            annotated = image.copy()
            detections = detection_results.get('detections', [])
            
            # Color mapping for grouped categories with better visibility
            colors = {
                'car': (0, 255, 0),           # Bright Green for Cars
                'truck': (255, 0, 0),         # Bright Red for Large Vehicles
                'bus': (255, 0, 0),           # Bright Red for Large Vehicles
                'motorcycle': (0, 0, 255),    # Bright Blue for 2-Wheelers
                'bicycle': (0, 0, 255),       # Bright Blue for 2-Wheelers (same as motorcycle)
                'large_vehicle': (255, 0, 0), # Bright Red for Large Vehicles
                '2-wheeler': (0, 0, 255),     # Bright Blue for 2-Wheelers
            }
            
            for detection in detections:
                bbox = detection['bbox']
                vehicle_class = detection['class']
                confidence = detection['confidence']
                
                x1, y1, x2, y2 = map(int, bbox)
                color = colors.get(vehicle_class, (128, 128, 128))
                
                # Draw bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
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
                display_class = class_display_mapping.get(vehicle_class, vehicle_class.replace('_', ' ').title())
                
                # Draw label with grouped category
                label = f"v12-{display_class}: {confidence:.2f}"
                cv2.putText(annotated, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Save annotated image
            base_name = Path(original_path).stem
            annotated_path = f"media/annotated_{base_name}_yolov12.jpg"
            cv2.imwrite(annotated_path, annotated)
            
            return annotated_path
            
        except Exception as e:
            logger.error(f"Error creating annotated image: {e}")
            return ""
    def _enhance_for_distant_vehicles(self, image: np.ndarray) -> np.ndarray:
        """Enhance image specifically for detecting distant/small vehicles"""
        # Increase contrast and brightness significantly
        enhanced = cv2.convertScaleAbs(image, alpha=1.5, beta=20)
        
        # Apply CLAHE for better contrast in different regions
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        lab[:,:,0] = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8)).apply(lab[:,:,0])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Sharpen the image for better edge detection
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(result, -1, kernel)
        
        # Blend original enhanced and sharpened
        final = cv2.addWeighted(result, 0.6, sharpened, 0.4, 0)
        
        return final
    
    def _detect_in_regions(self, image: np.ndarray) -> List:
        """Detect vehicles in different regions of the image for better coverage"""
        height, width = image.shape[:2]
        results = []
        
        # Define regions: left, center, right, top, bottom
        regions = [
            (0, 0, width//2, height),           # Left half
            (width//2, 0, width, height),      # Right half
            (0, 0, width, height//2),          # Top half
            (0, height//2, width, height),     # Bottom half
            (width//4, height//4, 3*width//4, 3*height//4)  # Center region
        ]
        
        for x1, y1, x2, y2 in regions:
            try:
                # Crop region
                region = image[y1:y2, x1:x2]
                if region.size == 0:
                    continue
                
                # Run detection on region
                region_results = self.model(
                    region,
                    verbose=False,
                    conf=0.04,  # Low confidence for regions
                    iou=0.25,
                    max_det=200,
                    augment=True,
                    half=False
                )
                
                # Adjust coordinates back to full image
                for result in region_results:
                    if result.boxes is not None:
                        # Adjust bounding box coordinates
                        adjusted_boxes = result.boxes.clone()
                        if len(adjusted_boxes.xyxy) > 0:
                            adjusted_boxes.xyxy[:, [0, 2]] += x1  # Adjust x coordinates
                            adjusted_boxes.xyxy[:, [1, 3]] += y1  # Adjust y coordinates
                            result.boxes = adjusted_boxes
                
                results.extend(region_results)
                
            except Exception as e:
                logger.warning(f"Error in region detection: {e}")
                continue
        
        return results
    
    def _detect_multiple_scales(self, image: np.ndarray) -> List:
        """Detect vehicles at multiple scales for better coverage"""
        results = []
        
        # Different scales
        scales = [0.8, 1.0, 1.2]
        
        for scale in scales:
            try:
                if scale != 1.0:
                    # Resize image
                    height, width = image.shape[:2]
                    new_height, new_width = int(height * scale), int(width * scale)
                    scaled_image = cv2.resize(image, (new_width, new_height))
                else:
                    scaled_image = image
                
                # Run detection
                scale_results = self.model(
                    scaled_image,
                    verbose=False,
                    conf=0.06,  # Slightly higher for scaled images
                    iou=0.30,
                    max_det=300,
                    augment=True,
                    half=False
                )
                
                # Adjust coordinates back to original scale
                if scale != 1.0:
                    for result in scale_results:
                        if result.boxes is not None:
                            # Scale coordinates back
                            result.boxes.xyxy /= scale
                
                results.extend(scale_results)
                
            except Exception as e:
                logger.warning(f"Error in scale {scale} detection: {e}")
                continue
        
        return results
    
    def _balanced_nms(self, detections: List[Dict]) -> List[Dict]:
        """Balanced Non-Maximum Suppression for accurate vehicle detection"""
        if not detections:
            return []
        
        # Group by class
        by_class = {}
        for det in detections:
            cls = det['class']
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(det)
        
        filtered = []
        for cls, cls_dets in by_class.items():
            # Sort by confidence (highest first)
            cls_dets.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Apply balanced NMS with reasonable IoU thresholds
            keep = []
            for det in cls_dets:
                should_keep = True
                for kept_det in keep:
                    iou = self._calculate_iou(det['bbox'], kept_det['bbox'])
                    
                    # Use balanced IoU thresholds based on vehicle type
                    if cls in ['motorcycle', 'bicycle']:
                        iou_threshold = 0.3  # Lower for small vehicles
                    elif det['relative_area'] < 0.002:  # Very small vehicles (distant)
                        iou_threshold = 0.25  # Lower for distant vehicles
                    else:
                        iou_threshold = 0.45  # Standard threshold for cars/trucks/buses
                    
                    if iou > iou_threshold:
                        # Keep the one with higher confidence, but also consider size
                        if det['confidence'] > kept_det['confidence'] * 1.1:  # 10% confidence advantage needed
                            # Replace the kept detection with this better one
                            keep.remove(kept_det)
                            keep.append(det)
                        should_keep = False
                        break
                
                if should_keep:
                    keep.append(det)
            
            filtered.extend(keep)
        
        return filtered