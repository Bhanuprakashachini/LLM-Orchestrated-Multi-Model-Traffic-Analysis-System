"""
YOLOv11 Traffic Analysis Service for Model Comparison
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class YOLOv11TrafficAnalyzer:
    """
    Traffic analysis service using YOLOv11 model for comparison
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu', confidence_threshold: float = 0.25, roi_polygon: Optional[List[Tuple[int, int]]] = None):  # Increased from 0.005
        """
        Initialize the YOLOv11 analyzer with balanced settings for accuracy and ROI filtering
        
        Args:
            model_path: Path to YOLO model file
            device: Device to run inference on ('cpu', 'cuda', or 'auto')
            confidence_threshold: Minimum confidence for detections (default: 0.25 for reliable detection)
            roi_polygon: List of (x, y) points defining the region of interest (road area)
        """
        self.device = device
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.roi_polygon = roi_polygon
        self.class_names = self._get_class_names()
        self.vehicle_classes = ['car', 'large_vehicle', '2-wheeler']  # Simplified 3 categories
        
        # Advanced configuration for maximum accuracy
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = 0.3  # Lower IoU for better detection of overlapping vehicles
        self.max_detections = 1000  # Increased for dense traffic
        self.agnostic_nms = True  # Better handling of different vehicle types
        
        # Enhanced vehicle class mapping - merge trucks and buses as large vehicles
        self.vehicle_class_mapping = {
            'car': 'car',
            'truck': 'large_vehicle',  # Merge trucks as large vehicles
            'bus': 'large_vehicle',    # Merge buses as large vehicles
            'train': 'large_vehicle',  # Trains as large vehicles (for trams/light rail)
            'motorcycle': '2-wheeler',  # Group as 2-wheeler
            'bicycle': '2-wheeler',     # Group as 2-wheeler
            'motorbike': '2-wheeler',   # Alternative name
            'van': 'large_vehicle',     # Classify vans as large vehicles
            'pickup': 'large_vehicle', # Pickup trucks as large vehicles
            'suv': 'car',  # SUVs as cars
            'sedan': 'car',  # Sedans as cars
            'hatchback': 'car',  # Hatchbacks as cars
            # Additional mappings for potential misclassifications
            'airplane': 'large_vehicle',  # Sometimes planes on ground are detected
            'boat': 'large_vehicle',     # Boats might be detected in some scenes
        }
        self.confidence_threshold = confidence_threshold
        
        # Load model if available
        try:
            self._load_model()
        except Exception as e:
            logger.warning(f"Could not load YOLOv11 model: {e}")
            logger.info("Using fallback detection method")
        
        logger.info(f"YOLOv11 analyzer initialized with confidence: {confidence_threshold}")
        if roi_polygon:
            logger.info(f"ROI polygon defined with {len(roi_polygon)} points")
    
    def _is_in_roi(self, centroid: Tuple[float, float], image_shape: Tuple[int, int]) -> bool:
        """
        Check if a detection centroid is within the region of interest
        
        Args:
            centroid: (x, y) coordinates of detection center
            image_shape: (height, width) of the image
            
        Returns:
            True if centroid is within ROI, False otherwise
        """
        if self.roi_polygon:
            # Use predefined ROI polygon
            point = (int(centroid[0]), int(centroid[1]))
            return cv2.pointPolygonTest(np.array(self.roi_polygon, dtype=np.int32), point, False) >= 0
        
        # If no ROI defined, use simple height-based filtering (assume road is in lower 70% of image)
        height_threshold = image_shape[0] * 0.3  # Top 30% is likely background/fields
        return centroid[1] > height_threshold
    
    def _filter_detections_by_roi(self, detections: List[Dict], image_shape: Tuple[int, int]) -> List[Dict]:
        """
        Filter detections to only include those within the region of interest
        
        Args:
            detections: List of detection dictionaries
            image_shape: (height, width) of the image
            
        Returns:
            Filtered list of detections within ROI
        """
        filtered_detections = []
        
        for detection in detections:
            # Calculate centroid from bbox
            bbox = detection.get('bbox', [])
            if len(bbox) >= 4:
                x1, y1, x2, y2 = bbox[:4]
                centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                
                if self._is_in_roi(centroid, image_shape):
                    filtered_detections.append(detection)
        
        logger.debug(f"ROI filtering: {len(detections)} -> {len(filtered_detections)} detections")
        return filtered_detections
    
    def _get_default_model_path(self) -> str:
        """Get default YOLOv11 model path - centralized to backend/models/"""
        from django.conf import settings
        
        # Try to use traffic-optimized model first
        traffic_model_path = Path(__file__).parent.parent.parent / 'models' / 'yolo11s_traffic.pt'
        if traffic_model_path.exists():
            return str(traffic_model_path)
        
        # Use centralized models directory
        centralized_model_path = Path(__file__).parent.parent.parent / 'models' / 'yolo11s.pt'
        if centralized_model_path.exists():
            return str(centralized_model_path)
        
        # Fallback to settings or default (should not be needed)
        return getattr(settings, 'YOLO11_MODEL_PATH', str(centralized_model_path))
    
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
        """Load YOLOv11 model"""
        try:
            from ultralytics import YOLO
            
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                logger.info(f"Loaded YOLOv11 model from {self.model_path}")
            else:
                # Use centralized model path as fallback
                centralized_path = Path(__file__).parent.parent.parent / 'models' / 'yolo11s.pt'
                if centralized_path.exists():
                    self.model = YOLO(str(centralized_path))
                    logger.info(f"Loaded YOLOv11 model from centralized location: {centralized_path}")
                else:
                    # Use absolute path to centralized model
                    abs_centralized_path = Path(__file__).resolve().parent.parent.parent / 'models' / 'yolo11s.pt'
                    if abs_centralized_path.exists():
                        self.model = YOLO(str(abs_centralized_path))
                        logger.info(f"Loaded YOLOv11 model from absolute centralized path: {abs_centralized_path}")
                    else:
                        raise FileNotFoundError(f"YOLOv11 model not found. Please ensure yolo11s.pt exists in backend/models/ directory")
                
        except ImportError:
            logger.error("Ultralytics not installed. Install with: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Failed to load YOLOv11 model: {e}")
            raise
    
    def analyze_traffic_scene(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a traffic scene image using YOLOv11
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            height, width = image.shape[:2]
            
            # Perform vehicle detection
            detection_results = self._detect_vehicles(image)
            
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
                    'model_version': 'YOLOv11',
                    'image_dimensions': {'width': width, 'height': height}
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing traffic scene with YOLOv11: {e}")
            return {
                'error': str(e),
                'vehicle_detection': {},
                'traffic_density': {},
                'performance_metrics': {
                    'processing_time': time.time() - start_time,
                    'fps': 0,
                    'model_version': 'YOLOv11',
                    'error': True
                }
            }
    
    def _detect_vehicles(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect vehicles in the image using YOLOv11 with advanced multi-strategy approach
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary containing detection results
        """
        try:
            if self.model is None:
                logger.error("YOLOv11 model is None - using fallback detection")
                return self._fallback_detection(image)
            
            logger.info(f"YOLOv11 model loaded successfully, running multi-strategy inference...")
            
            # Strategy 1: Reasonable confidence for dense traffic detection
            results_ultra_low = self.model(image, verbose=False, conf=0.05)  # Increased from 0.01
            
            # Strategy 2: Standard inference
            results = self.model(image, verbose=False, conf=self.confidence_threshold)
            
            # Strategy 3: Multi-scale inference (resize image for better detection)
            image_resized_small = cv2.resize(image, (640, 640))  # Smaller for distant vehicles
            results_small = self.model(image_resized_small, verbose=False, conf=0.05)  # Ultra-low for small vehicles
            
            image_resized_medium = cv2.resize(image, (1280, 1280))  # YOLO optimal size
            results_medium = self.model(image_resized_medium, verbose=False, conf=0.05)  # Ultra-low confidence
            
            image_resized_large = cv2.resize(image, (1920, 1920))  # Large for close vehicles
            results_large = self.model(image_resized_large, verbose=False, conf=0.05)  # Ultra-low confidence
            
            # Strategy 4: Image enhancement for better detection
            enhanced_image = self._enhance_image_for_detection(image)
            results_enhanced = self.model(enhanced_image, verbose=False, conf=0.05)  # Ultra-low confidence
            
            # Strategy 5: Contrast enhanced image
            contrast_enhanced = self._enhance_contrast(image)
            results_contrast = self.model(contrast_enhanced, verbose=False, conf=0.05)  # Ultra-low confidence
            
            # Strategy 6: Brightness adjusted images
            bright_image = cv2.convertScaleAbs(image, alpha=1.2, beta=20)
            results_bright = self.model(bright_image, verbose=False, conf=0.05)  # Ultra-low confidence
            
            dark_image = cv2.convertScaleAbs(image, alpha=0.8, beta=-20)
            results_dark = self.model(dark_image, verbose=False, conf=0.05)  # Ultra-low confidence
            
            # Strategy 7: Different aspect ratios for highway scenes
            height, width = image.shape[:2]
            if width > height * 1.5:  # Likely highway scene
                # Crop to focus on traffic areas
                crop_top = image[0:int(height*0.8), :]  # Top 80%
                crop_bottom = image[int(height*0.2):, :]  # Bottom 80%
                results_crop_top = self.model(crop_top, verbose=False, conf=0.05)
                results_crop_bottom = self.model(crop_bottom, verbose=False, conf=0.05)
            else:
                results_crop_top = []
                results_crop_bottom = []
            
            # Strategy 8: Enhanced 2-wheeler detection with ultra-low confidence
            results_2wheeler_ultra = self.model(image, verbose=False, conf=0.03)  # Ultra-low for 2-wheelers
            
            # Strategy 9: 2-wheeler focused image enhancement
            enhanced_2wheeler = self._enhance_for_2wheelers(image)
            results_2wheeler_enhanced = self.model(enhanced_2wheeler, verbose=False, conf=0.05)  # Ultra-low confidence
            
            detections = []
            vehicle_counts = {'car': 0, 'large_vehicle': 0, '2-wheeler': 0}
            total_confidence = 0
            filtered_count = 0  # Track filtered detections
            all_detections_count = 0  # Track all detections before filtering
            
            logger.info(f"YOLOv11 running multi-strategy inference for maximum accuracy including enhanced 2-wheeler detection")
            
            all_detections = []
            processed_boxes = set()
            
            # Apply more reasonable confidence thresholds to reduce false positives
            inference_results = [
                ("standard", results),  # Only use standard inference with reasonable confidence
                ("enhanced", results_enhanced),  # Use enhanced image
            ]
            
            # Remove ultra-low confidence strategies that cause false positives
            # ("ultra_low", results_ultra_low),  # DISABLED - causes too many false positives
            # ("small_scale", results_small),    # DISABLED - causes duplicate detections
            # ("medium_scale", results_medium),  # DISABLED - causes duplicate detections
            # ("large_scale", results_large),    # DISABLED - causes duplicate detections
            # ("contrast", results_contrast),    # DISABLED - causes false positives
            # ("bright", results_bright),        # DISABLED - causes false positives
            # ("dark", results_dark),            # DISABLED - causes false positives
            # ("2wheeler_ultra", results_2wheeler_ultra),      # DISABLED - ultra-low confidence
            # ("2wheeler_enhanced", results_2wheeler_enhanced) # DISABLED - causes false positives
            
            # Add crop results if available
            if results_crop_top:
                inference_results.append(("crop_top", results_crop_top))
            if results_crop_bottom:
                inference_results.append(("crop_bottom", results_crop_bottom))
            
            for strategy_name, strategy_results in inference_results:
                logger.info(f"Processing {strategy_name} inference results...")
                
                for result in strategy_results:
                    boxes = result.boxes
                    if boxes is not None:
                        logger.info(f"{strategy_name}: {len(boxes)} detections found")
                        
                        for box in boxes:
                            try:
                                all_detections_count += 1
                                class_id = int(box.cls[0])
                                confidence = float(box.conf[0])
                                mapped_class = None  # Initialize to avoid scope issues
                                
                                if class_id < len(self.class_names):
                                    class_name = self.class_names[class_id]
                                    
                                    # Only process vehicle classes that can be mapped
                                    if class_name in self.vehicle_class_mapping:
                                        # Map to standard vehicle class
                                        mapped_class = self.vehicle_class_mapping.get(class_name, class_name)
                                        if mapped_class not in self.vehicle_classes:
                                            continue  # Skip if not a recognized vehicle type
                                    else:
                                        # Skip non-vehicle objects (person, bicycle, etc.)
                                        continue
                                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                                    
                                    # Scale coordinates back if from different sized images
                                    if strategy_name == "small_scale":
                                        scale_x = image.shape[1] / 640
                                        scale_y = image.shape[0] / 640
                                        x1, x2 = x1 * scale_x, x2 * scale_x
                                        y1, y2 = y1 * scale_y, y2 * scale_y
                                    elif strategy_name == "medium_scale":
                                        scale_x = image.shape[1] / 1280
                                        scale_y = image.shape[0] / 1280
                                        x1, x2 = x1 * scale_x, x2 * scale_x
                                        y1, y2 = y1 * scale_y, y2 * scale_y
                                    elif strategy_name == "large_scale":
                                        scale_x = image.shape[1] / 1920
                                        scale_y = image.shape[0] / 1920
                                        x1, x2 = x1 * scale_x, x2 * scale_x
                                        y1, y2 = y1 * scale_y, y2 * scale_y
                                    elif strategy_name == "crop_top":
                                        # No X scaling needed, but Y needs offset
                                        pass  # Coordinates are already correct for top crop
                                    elif strategy_name == "crop_bottom":
                                        # Add Y offset for bottom crop
                                        y_offset = int(image.shape[0] * 0.2)
                                        y1, y2 = y1 + y_offset, y2 + y_offset
                                    
                                    # Create unique box identifier
                                    box_center = ((x1 + x2) / 2, (y1 + y2) / 2)
                                    box_size = (x2 - x1) * (y2 - y1)
                                    
                                    # Stricter duplicate detection to prevent multiple detections of same vehicle
                                    is_duplicate = False
                                    for existing_center, existing_size in processed_boxes:
                                        center_distance = ((box_center[0] - existing_center[0])**2 + 
                                                         (box_center[1] - existing_center[1])**2)**0.5
                                        size_ratio = min(box_size, existing_size) / max(box_size, existing_size)
                                        
                                        # Much stricter duplicate detection
                                        if center_distance < 50 and size_ratio > 0.5:  # Increased distance threshold
                                            is_duplicate = True
                                            break
                                    
                                    # Apply stricter confidence thresholds to reduce false positives
                                    if strategy_name in ["enhanced"]:
                                        min_confidence = 0.3  # Higher threshold for enhanced detection
                                    else:
                                        min_confidence = 0.4  # Much higher base confidence to reduce false positives
                                    
                                    if not is_duplicate and confidence >= min_confidence:
                                        detection = {
                                            'class': mapped_class,  # Use mapped class
                                            'original_class': class_name,  # Keep original for reference
                                            'confidence': confidence,
                                            'bbox': {
                                                'x1': int(x1), 'y1': int(y1),
                                                'x2': int(x2), 'y2': int(y2)
                                            },
                                            'area': (x2 - x1) * (y2 - y1),
                                            'detection_strategy': strategy_name,
                                            'vehicle_details': self._get_vehicle_details(mapped_class, confidence, (x2-x1)*(y2-y1))
                                        }
                                        
                                        # Intelligent SUV/Truck reclassification
                                        if mapped_class == 'truck':
                                            reclassified_class = self._intelligent_truck_classification(detection, image)
                                            if reclassified_class != 'truck':
                                                detection['class'] = reclassified_class
                                                detection['reclassified'] = True
                                                detection['reclassification_reason'] = f"Size/confidence analysis suggests {reclassified_class}"
                                                mapped_class = reclassified_class  # Update for counting
                                        
                                        # 🎯 APPLY ROI FILTERING - Check if detection is within region of interest
                                        centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                                        if not self._is_in_roi(centroid, image.shape[:2]):
                                            logger.debug(f"Detection filtered by ROI: {mapped_class} at {centroid}")
                                            filtered_count += 1
                                            continue  # Skip this detection as it's outside ROI
                                        
                                        detections.append(detection)
                                        vehicle_counts[mapped_class] += 1  # Use mapped class for counting
                                        total_confidence += confidence
                                        processed_boxes.add((box_center, box_size))
                                        
                                        logger.info(f"Vehicle detected ({strategy_name}): {mapped_class} (confidence: {confidence:.3f})")
                                    elif is_duplicate and mapped_class:
                                        logger.debug(f"Duplicate detection filtered: {mapped_class}")
                                    else:
                                        filtered_count += 1
                            except Exception as box_error:
                                logger.warning(f"Error processing detection box in {strategy_name}: {box_error}")
                                continue  # Skip this detection but continue with others
            
            avg_confidence = total_confidence / len(detections) if detections else 0
            total_vehicles = sum(vehicle_counts.values())
            
            logger.info(f"YOLOv11 SUMMARY: {total_vehicles} vehicles detected from {all_detections_count} total detections (filtered {filtered_count} low-confidence)")
            
            return {
                'detections': detections,
                'vehicle_counts': vehicle_counts,
                'total_vehicles': total_vehicles,
                'average_confidence': avg_confidence,
                'filtered_detections': filtered_count,
                'confidence_threshold': self.confidence_threshold,
                'detection_summary': {
                    'cars': vehicle_counts['car'],
                    'large_vehicles': vehicle_counts['large_vehicle'],
                    '2_wheelers': vehicle_counts['2-wheeler']
                },
                'vehicle_breakdown': self._generate_vehicle_breakdown(detections),
                'detection_strategies_used': list(set(d['detection_strategy'] for d in detections))
            }
            
        except Exception as e:
            logger.error(f"Error in YOLOv11 vehicle detection: {e}")
            return self._fallback_detection(image)
    
    def _fallback_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Fallback detection method when YOLOv11 is not available
        Uses enhanced OpenCV-based detection optimized for YOLOv11 characteristics
        """
        logger.warning("YOLOv11 model not available - using enhanced OpenCV fallback detection")
        
        try:
            height, width = image.shape[:2]
            
            # Enhanced OpenCV-based vehicle detection (YOLOv11 style)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (3, 3), 0)  # Smaller kernel for better detail
            
            # Use adaptive threshold for better edge detection
            adaptive_thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                  cv2.THRESH_BINARY, 11, 2)
            
            # Morphological operations to clean up the image
            kernel = np.ones((3, 3), np.uint8)
            cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            vehicle_counts = {'car': 0, 'large_vehicle': 0, '2-wheeler': 0}
            
            # Enhanced filtering for better vehicle detection
            for contour in contours:
                area = cv2.contourArea(contour)
                if 800 < area < 60000:  # Slightly wider range for YOLOv11
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Enhanced classification logic
                    aspect_ratio = w / h if h > 0 else 0
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                    
                    # More sophisticated classification
                    if area > 20000 and aspect_ratio > 1.5:
                        vehicle_class = 'bus'
                        confidence = min(0.75, 0.5 + (area / 60000) * 0.25)
                    elif area > 12000 and 1.2 < aspect_ratio < 3.0:
                        vehicle_class = 'truck'
                        confidence = min(0.70, 0.45 + (area / 40000) * 0.25)
                    elif 0.8 < aspect_ratio < 2.8 and area > 4000:
                        vehicle_class = 'car'
                        confidence = min(0.65, 0.4 + (area / 30000) * 0.25)
                    elif area < 4000 and aspect_ratio > 0.5:
                        vehicle_class = 'motorcycle'
                        confidence = min(0.60, 0.35 + (area / 8000) * 0.25)
                    elif area < 2000 and 0.3 < aspect_ratio < 1.5:
                        vehicle_class = 'bicycle'
                        confidence = min(0.55, 0.3 + (area / 4000) * 0.25)
                    else:
                        continue  # Skip unclear detections
                    
                    # Boost confidence for well-formed rectangles
                    if 0.6 < circularity < 0.9:
                        confidence = min(confidence + 0.1, 0.75)
                    
                    detection = {
                        'class': vehicle_class,
                        'confidence': confidence,
                        'bbox': {'x1': x, 'y1': y, 'x2': x + w, 'y2': y + h},
                        'area': area
                    }
                    
                    detections.append(detection)
                    vehicle_counts[vehicle_class] += 1
            
            total_vehicles = sum(vehicle_counts.values())
            avg_confidence = sum(d['confidence'] for d in detections) / len(detections) if detections else 0
            
            logger.info(f"Enhanced OpenCV fallback (YOLOv11 style) detected {total_vehicles} potential vehicles")
            
            return {
                'detections': detections,
                'vehicle_counts': vehicle_counts,
                'total_vehicles': total_vehicles,
                'average_confidence': avg_confidence,
                'detection_summary': vehicle_counts,
                'fallback_mode': True,
                'fallback_method': 'opencv_enhanced'
            }
            
        except Exception as e:
            logger.error(f"Enhanced OpenCV fallback detection failed: {e}")
            
            # Last resort - return empty results with error
            return {
                'detections': [],
                'vehicle_counts': {'car': 0, 'large_vehicle': 0, '2-wheeler': 0},
                'total_vehicles': 0,
                'average_confidence': 0.0,
                'detection_summary': {'car': 0, 'large_vehicle': 0, '2-wheeler': 0},
                'fallback_mode': True,
                'fallback_method': 'failed',
                'error': str(e)
            }
    
    def _analyze_traffic_density(self, detection_results: Dict[str, Any], image_size: Tuple[int, int]) -> Dict[str, Any]:
        """
        Analyze traffic density based on detection results
        
        Args:
            detection_results: Results from vehicle detection
            image_size: (width, height) of the image
            
        Returns:
            Dictionary containing density analysis
        """
        width, height = image_size
        image_area = width * height
        
        total_vehicles = detection_results.get('total_vehicles', 0)
        detections = detection_results.get('detections', [])
        
        # Calculate vehicle density per square meter
        vehicle_density = total_vehicles / (image_area / 1000000)
        
        # Calculate area coverage by vehicles
        total_vehicle_area = sum(det.get('area', 0) for det in detections)
        area_coverage_percentage = (total_vehicle_area / image_area) * 100
        
        # Determine density level with realistic thresholds for different traffic scenarios
        if total_vehicles == 0:
            density_level = 'Empty'
            congestion_index = 0.0
        elif total_vehicles <= 3:
            density_level = 'Very Light'
            congestion_index = 0.1
        elif total_vehicles <= 8:
            density_level = 'Light'
            congestion_index = 0.2
        elif total_vehicles <= 20:
            density_level = 'Moderate'
            congestion_index = 0.4
        elif total_vehicles <= 40:
            density_level = 'Heavy'
            congestion_index = 0.6
        elif total_vehicles <= 80:
            density_level = 'Very Heavy'
            congestion_index = 0.8
        elif total_vehicles <= 150:
            density_level = 'Dense'
            congestion_index = 0.9
        else:
            density_level = 'Extremely Dense'
            congestion_index = 1.0
        
        # Adjust based on area coverage
        if area_coverage_percentage > 22:
            if density_level in ['Low', 'Medium']:
                density_level = 'High'
                congestion_index = min(congestion_index + 0.25, 1.0)
            elif density_level == 'High':
                density_level = 'Congested'
                congestion_index = 1.0
        
        return {
            'density_level': density_level,
            'congestion_index': congestion_index,
            'vehicle_density': vehicle_density,
            'area_coverage_percentage': area_coverage_percentage,
            'total_vehicles': total_vehicles,
            'density_metrics': {
                'vehicles_per_area': vehicle_density,
                'coverage_percentage': area_coverage_percentage,
                'congestion_score': congestion_index * 100
            }
        }
    
    def _create_annotated_image(self, image: np.ndarray, detection_results: Dict[str, Any], original_path: str) -> str:
        """
        Create annotated image with bounding boxes
        
        Args:
            image: Original image
            detection_results: Detection results
            original_path: Path to original image
            
        Returns:
            Path to annotated image
        """
        try:
            annotated_image = image.copy()
            detections = detection_results.get('detections', [])
            
            # Filter detections using the same confidence thresholds as detection logic
            # 2-wheeler strategies use 0.03, others use 0.05
            filtered_detections = []
            for d in detections:
                strategy = d.get('detection_strategy', '')
                if strategy in ["2wheeler_ultra", "2wheeler_enhanced"] and d['class'] == '2-wheeler':
                    min_confidence = 0.03  # Lower threshold for 2-wheelers
                else:
                    min_confidence = 0.05  # Standard threshold for cars and large vehicles
                
                if d['confidence'] >= min_confidence:
                    filtered_detections.append(d)
            
            # Apply the same deduplication logic used in detection
            deduplicated_detections = []
            for detection in filtered_detections:
                is_duplicate = False
                
                for existing in deduplicated_detections:
                    # Calculate center distance
                    center1 = (
                        (detection['bbox']['x1'] + detection['bbox']['x2']) / 2,
                        (detection['bbox']['y1'] + detection['bbox']['y2']) / 2
                    )
                    center2 = (
                        (existing['bbox']['x1'] + existing['bbox']['x2']) / 2,
                        (existing['bbox']['y1'] + existing['bbox']['y2']) / 2
                    )
                    center_distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
                    
                    # Calculate size ratio
                    area1 = (detection['bbox']['x2'] - detection['bbox']['x1']) * (detection['bbox']['y2'] - detection['bbox']['y1'])
                    area2 = (existing['bbox']['x2'] - existing['bbox']['x1']) * (existing['bbox']['y2'] - existing['bbox']['y1'])
                    size_ratio = min(area1, area2) / max(area1, area2) if max(area1, area2) > 0 else 0
                    
                    # Same deduplication criteria as detection logic
                    if center_distance < 20 and size_ratio > 0.7:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    deduplicated_detections.append(detection)
            
            # Use deduplicated detections for annotation
            filtered_detections = deduplicated_detections
            
            # LIMIT ANNOTATIONS FOR PERFORMANCE - Only show top detections when there are too many
            MAX_ANNOTATIONS = 50  # Limit to prevent memory/performance issues
            if len(filtered_detections) > MAX_ANNOTATIONS:
                # Sort by confidence and take top detections
                filtered_detections = sorted(filtered_detections, key=lambda x: x['confidence'], reverse=True)[:MAX_ANNOTATIONS]
                logger.info(f"YOLOv11: Limited annotations to top {MAX_ANNOTATIONS} detections (out of {len(deduplicated_detections)} total)")
            
            logger.info(f"YOLOv11: Creating annotated image with {len(filtered_detections)} annotations")
            
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
            
            for detection in filtered_detections:
                bbox = detection['bbox']
                class_name = detection['class']
                confidence = detection['confidence']
                
                # Get color for this vehicle type
                color = colors.get(class_name, (220, 220, 220))
                
                # Draw bounding box
                cv2.rectangle(
                    annotated_image,
                    (bbox['x1'], bbox['y1']),
                    (bbox['x2'], bbox['y2']),
                    color,
                    2
                )
                
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
                label = f"v11-{display_class}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                
                cv2.rectangle(
                    annotated_image,
                    (bbox['x1'], bbox['y1'] - label_size[1] - 10),
                    (bbox['x1'] + label_size[0], bbox['y1']),
                    color,
                    -1
                )
                
                cv2.putText(
                    annotated_image,
                    label,
                    (bbox['x1'], bbox['y1'] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2
                )
            
            # Add summary overlay when annotations are limited
            if len(deduplicated_detections) > len(filtered_detections):
                # Add semi-transparent background for summary
                overlay = annotated_image.copy()
                cv2.rectangle(overlay, (10, 10), (450, 80), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, annotated_image, 0.3, 0, annotated_image)
                
                # Add summary text
                summary_text = f"YOLOv11: Showing top {len(filtered_detections)} of {len(deduplicated_detections)} detections"
                cv2.putText(annotated_image, summary_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                total_text = f"Total vehicles detected: {len(deduplicated_detections)}"
                cv2.putText(annotated_image, total_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Save annotated image with better error handling
            original_name = Path(original_path).stem
            annotated_path = str(Path(original_path).parent / f"{original_name}_yolov11_annotated.jpg")
            
            # Optimize image size for large images to prevent memory issues
            height, width = annotated_image.shape[:2]
            if width > 1920 or height > 1080:
                # Resize large images to prevent memory issues
                scale = min(1920/width, 1080/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                annotated_image = cv2.resize(annotated_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.info(f"YOLOv11: Resized annotated image from {width}x{height} to {new_width}x{new_height}")
            
            # Save with compression to reduce file size
            success = cv2.imwrite(annotated_path, annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            if not success:
                logger.error(f"YOLOv11: Failed to save annotated image to {annotated_path}")
                return original_path
            
            # Verify file was created and is accessible
            if not os.path.exists(annotated_path):
                logger.error(f"YOLOv11: Annotated image file not found after save: {annotated_path}")
                return original_path
                
            file_size = os.path.getsize(annotated_path)
            logger.info(f"YOLOv11: Successfully saved annotated image: {annotated_path} ({file_size} bytes)")
            
            return annotated_path
            
        except Exception as e:
            logger.error(f"Error creating YOLOv11 annotated image: {e}")
            return original_path
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast for better vehicle detection
        """
        try:
            # Convert to YUV color space
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            
            # Apply histogram equalization to Y channel
            yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}, using original image")
            return image
    
    def _enhance_image_for_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image for better vehicle detection
        """
        try:
            # Convert to LAB color space for better contrast enhancement
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge channels and convert back to BGR
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            # Apply slight sharpening
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            
            # Ensure values are in valid range
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}, using original image")
            return image
    
    def _intelligent_truck_classification(self, detection: Dict, image: np.ndarray) -> str:
        """
        Intelligently reclassify trucks that might be SUVs or large cars
        
        Args:
            detection: Detection dictionary with bbox and confidence
            image: Original image for context
            
        Returns:
            Reclassified vehicle type ('car' or 'truck')
        """
        try:
            bbox = detection['bbox']
            confidence = detection['confidence']
            area = detection['area']
            
            # Calculate vehicle dimensions
            width = bbox['x2'] - bbox['x1']
            height = bbox['y2'] - bbox['y1']
            aspect_ratio = width / height if height > 0 else 1.0
            
            # Get image dimensions for relative size analysis
            img_height, img_width = image.shape[:2]
            relative_width = width / img_width
            relative_height = height / img_height
            relative_area = area / (img_width * img_height)
            
            # Reclassification logic based on multiple factors
            car_score = 0
            truck_score = 0
            
            # Factor 1: Confidence level (low confidence trucks are often misclassified SUVs)
            if confidence < 0.6:
                car_score += 3  # Strong indicator of misclassification
            elif confidence < 0.7:
                car_score += 1
            else:
                truck_score += 1
            
            # Factor 2: Size analysis (trucks should be significantly larger)
            if relative_area < 0.02:  # Very small relative to image - likely car
                car_score += 2
            elif relative_area < 0.05:  # Small to medium - could be SUV
                car_score += 1
            elif relative_area > 0.15:  # Very large - likely actual truck
                truck_score += 2
            
            # Factor 3: Aspect ratio (trucks tend to be longer/wider)
            if aspect_ratio > 2.0:  # Very wide - likely truck
                truck_score += 2
            elif aspect_ratio > 1.5:  # Moderately wide - could be either
                pass  # Neutral
            else:  # More square/tall - likely car/SUV
                car_score += 1
            
            # Factor 4: Relative height (trucks should be taller)
            if relative_height < 0.15:  # Short relative to image - likely car
                car_score += 2
            elif relative_height < 0.25:  # Medium height - could be SUV
                car_score += 1
            
            # Factor 5: Position in image (trucks often appear larger when closer)
            center_y = (bbox['y1'] + bbox['y2']) / 2
            relative_y = center_y / img_height
            
            if relative_y > 0.7:  # Lower in image (closer) - size might be misleading
                if relative_area > 0.1:  # Large and close - could be car appearing large
                    car_score += 1
            
            # Decision logic
            if car_score > truck_score + 1:  # Clear preference for car
                logger.info(f"Reclassifying truck to car (car_score: {car_score}, truck_score: {truck_score}, confidence: {confidence:.3f})")
                return 'car'
            else:
                return 'truck'
                
        except Exception as e:
            logger.error(f"Error in intelligent truck classification: {e}")
            return 'truck'  # Default to original classification

    def _get_vehicle_details(self, vehicle_class: str, confidence: float, area: float) -> Dict[str, Any]:
        """Get detailed information about detected vehicle"""
        
        # Vehicle size categories based on bounding box area
        if area < 5000:
            size_category = 'small'
        elif area < 15000:
            size_category = 'medium'
        elif area < 30000:
            size_category = 'large'
        else:
            size_category = 'very_large'
        
        # Vehicle descriptions
        descriptions = {
            'car': {
                'small': 'Compact car or distant vehicle',
                'medium': 'Standard passenger car',
                'large': 'Large sedan or SUV',
                'very_large': 'Large SUV or close vehicle'
            },
            'truck': {
                'small': 'Pickup truck or van',
                'medium': 'Delivery truck or large van',
                'large': 'Commercial truck',
                'very_large': 'Large commercial vehicle or semi-truck'
            },
            'bus': {
                'small': 'Minibus or shuttle',
                'medium': 'City bus',
                'large': 'Large transit bus',
                'very_large': 'Articulated bus or coach'
            },
            'motorcycle': {
                'small': 'Scooter or small motorcycle',
                'medium': 'Standard motorcycle',
                'large': 'Large motorcycle or touring bike',
                'very_large': 'Large touring motorcycle'
            },
            'bicycle': {
                'small': 'Bicycle',
                'medium': 'Bicycle with rider',
                'large': 'Bicycle with accessories',
                'very_large': 'Multiple bicycles or cargo bike'
            }
        }
        
        # Confidence level description
        if confidence >= 0.8:
            confidence_level = 'very_high'
            confidence_desc = 'Very confident detection'
        elif confidence >= 0.6:
            confidence_level = 'high'
            confidence_desc = 'High confidence detection'
        elif confidence >= 0.4:
            confidence_level = 'medium'
            confidence_desc = 'Medium confidence detection'
        elif confidence >= 0.2:
            confidence_level = 'low'
            confidence_desc = 'Low confidence detection'
        else:
            confidence_level = 'very_low'
            confidence_desc = 'Very low confidence detection'
        
        return {
            'type': vehicle_class,
            'size_category': size_category,
            'description': descriptions.get(vehicle_class, {}).get(size_category, f'{(vehicle_class or "unknown").title()}'),
            'confidence_level': confidence_level,
            'confidence_description': confidence_desc,
            'area_pixels': int(area),
            'detection_quality': 'excellent' if confidence >= 0.7 else 'good' if confidence >= 0.5 else 'fair' if confidence >= 0.3 else 'poor'
        }
    
    def _generate_vehicle_breakdown(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed breakdown of detected vehicles"""
        
        breakdown = {
            'by_type': {},
            'by_confidence': {'high': 0, 'medium': 0, 'low': 0},
            'by_size': {'small': 0, 'medium': 0, 'large': 0, 'very_large': 0},
            'detailed_list': []
        }
        
        for i, detection in enumerate(detections):
            vehicle_class = detection['class']
            confidence = detection['confidence']
            details = detection.get('vehicle_details', {})
            
            # Count by type
            if vehicle_class not in breakdown['by_type']:
                breakdown['by_type'][vehicle_class] = {
                    'count': 0,
                    'avg_confidence': 0,
                    'confidence_range': {'min': 1.0, 'max': 0.0},
                    'sizes': {'small': 0, 'medium': 0, 'large': 0, 'very_large': 0}
                }
            
            type_info = breakdown['by_type'][vehicle_class]
            type_info['count'] += 1
            type_info['confidence_range']['min'] = min(type_info['confidence_range']['min'], confidence)
            type_info['confidence_range']['max'] = max(type_info['confidence_range']['max'], confidence)
            
            # Update size counts
            size_cat = details.get('size_category', 'medium')
            type_info['sizes'][size_cat] += 1
            breakdown['by_size'][size_cat] += 1
            
            # Count by confidence level
            if confidence >= 0.6:
                breakdown['by_confidence']['high'] += 1
            elif confidence >= 0.3:
                breakdown['by_confidence']['medium'] += 1
            else:
                breakdown['by_confidence']['low'] += 1
            
            # Add to detailed list
            breakdown['detailed_list'].append({
                'id': i + 1,
                'type': vehicle_class,
                'description': details.get('description', (vehicle_class or "unknown").title()),
                'confidence': f"{confidence:.1%}",
                'confidence_level': details.get('confidence_level', 'medium'),
                'size': details.get('size_category', 'medium'),
                'quality': details.get('detection_quality', 'good'),
                'bbox_area': details.get('area_pixels', 0)
            })
        
        # Calculate average confidences
        for vehicle_class, info in breakdown['by_type'].items():
            class_detections = [d for d in detections if d['class'] == vehicle_class]
            if class_detections:
                info['avg_confidence'] = sum(d['confidence'] for d in class_detections) / len(class_detections)
        
        return breakdown
    
    def _enhance_for_2wheelers(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image specifically for better 2-wheeler (motorcycle/bicycle) detection
        """
        try:
            # Convert to grayscale for edge detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter to reduce noise while preserving edges
            filtered = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Enhance edges using unsharp masking
            gaussian = cv2.GaussianBlur(filtered, (0, 0), 2.0)
            unsharp_mask = cv2.addWeighted(filtered, 1.5, gaussian, -0.5, 0)
            
            # Convert back to BGR
            enhanced_gray = cv2.cvtColor(unsharp_mask, cv2.COLOR_GRAY2BGR)
            
            # Combine with original image to preserve color information
            enhanced = cv2.addWeighted(image, 0.7, enhanced_gray, 0.3, 0)
            
            # Apply morphological operations to enhance small objects (2-wheelers)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
            
            # Increase contrast specifically for small objects
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE with smaller tile size for better small object detection
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
            l = clahe.apply(l)
            
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            # Ensure values are in valid range
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
            
            logger.debug("Applied 2-wheeler specific image enhancement")
            return enhanced
            
        except Exception as e:
            logger.warning(f"2-wheeler image enhancement failed: {e}, using original image")
            return image
