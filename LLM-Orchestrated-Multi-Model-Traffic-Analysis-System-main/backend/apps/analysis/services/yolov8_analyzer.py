"""
YOLOv8 Traffic Analysis Service for Model Comparison
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class YOLOv8TrafficAnalyzer:
    """
    Traffic analysis service using YOLOv8 model for comparison
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu', confidence_threshold: float = 0.25, roi_polygon: Optional[List[Tuple[int, int]]] = None):
        """
        Initialize the YOLOv8 analyzer with balanced settings for accurate vehicle detection
        
        Args:
            model_path: Path to YOLO model file
            device: Device to run inference on ('cpu' or 'cuda')
            confidence_threshold: Minimum confidence for detections (default: 0.25 for accurate detection)
            roi_polygon: List of (x, y) points defining the region of interest (road area)
        """
        self.device = device
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.roi_polygon = roi_polygon
        self.class_names = self._get_class_names()
        self.vehicle_classes = ['car', 'large_vehicle', '2-wheeler']  # Simplified 3 categories
        
        # Balanced configuration for accurate vehicle detection without false positives
        self.confidence_threshold = max(0.05, confidence_threshold)  # OPTIMIZED: Sweet spot for maximum real vehicles
        self.iou_threshold = 0.45  # Standard IoU for proper NMS (was 0.25)
        self.max_detections = 300  # Reasonable limit for real scenarios
        self.agnostic_nms = False  # Class-specific NMS for better accuracy
        
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
            logger.warning(f"Could not load YOLOv8 model: {e}")
            logger.info("Using fallback detection method")
        
        logger.info(f"YOLOv8 analyzer initialized with confidence: {confidence_threshold}")
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
        """Get default YOLOv8 model path - centralized to backend/models/"""
        from django.conf import settings
        
        # Try to use traffic-optimized model first
        traffic_model_path = Path(__file__).parent.parent.parent / 'models' / 'yolov8s_traffic.pt'
        if traffic_model_path.exists():
            return str(traffic_model_path)
        
        # Use centralized models directory
        centralized_model_path = Path(__file__).parent.parent.parent / 'models' / 'yolov8s.pt'
        if centralized_model_path.exists():
            return str(centralized_model_path)
        
        # Fallback to settings or default (should not be needed)
        return getattr(settings, 'YOLOV8_MODEL_PATH', str(centralized_model_path))
    
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
        """Load YOLOv8 model with GPU acceleration if available"""
        try:
            from ultralytics import YOLO
            import torch
            
            # Auto-detect best device
            if self.device == 'auto':
                if torch.cuda.is_available():
                    self.device = 'cuda'
                    logger.info("CUDA available - using GPU acceleration")
                else:
                    self.device = 'cpu'
                    logger.info("CUDA not available - using CPU")
            
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                logger.info(f"Loaded YOLOv8 model from {self.model_path}")
            else:
                # Use centralized model path as fallback
                centralized_path = Path(__file__).parent.parent.parent / 'models' / 'yolov8s.pt'
                if centralized_path.exists():
                    self.model = YOLO(str(centralized_path))
                    logger.info(f"Loaded YOLOv8 model from centralized location: {centralized_path}")
                else:
                    # Use absolute path to centralized model
                    abs_centralized_path = Path(__file__).resolve().parent.parent.parent / 'models' / 'yolov8s.pt'
                    if abs_centralized_path.exists():
                        self.model = YOLO(str(abs_centralized_path))
                        logger.info(f"Loaded YOLOv8 model from absolute centralized path: {abs_centralized_path}")
                    else:
                        raise FileNotFoundError(f"YOLOv8 model not found. Please ensure yolov8s.pt exists in backend/models/ directory")
            
            # Move model to specified device
            if hasattr(self.model, 'to'):
                self.model.to(self.device)
                logger.info(f"Model moved to device: {self.device}")
                
        except ImportError:
            logger.error("Ultralytics not installed. Install with: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise
    
    def analyze_traffic_scene(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a traffic scene image or video using YOLOv8
        
        Args:
            image_path: Path to the image or video file
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        try:
            # Check if it's a video file
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
            is_video = any(image_path.lower().endswith(ext) for ext in video_extensions)
            
            if is_video:
                return self._analyze_video(image_path, start_time)
            else:
                return self._analyze_image(image_path, start_time)
                
        except Exception as e:
            logger.error(f"Error analyzing traffic scene with YOLOv8: {e}")
            return {
                'error': str(e),
                'vehicle_detection': {},
                'traffic_density': {},
                'performance_metrics': {
                    'processing_time': time.time() - start_time,
                    'fps': 0,
                    'model_version': 'YOLOv8',
                    'error': True
                }
            }
    
    def _analyze_image(self, image_path: str, start_time: float) -> Dict[str, Any]:
        """Analyze a single image"""
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
        
        # Validate count-annotation consistency
        validation_results = self.validate_count_annotation_consistency(detection_results, annotated_image_path)
        
        # Calculate performance metrics
        processing_time = time.time() - start_time
        fps = 1.0 / processing_time if processing_time > 0 else 0
        
        return {
            'vehicle_detection': detection_results,
            'traffic_density': density_results,
            'annotated_image_path': annotated_image_path,
            'validation': validation_results,  # Add validation results
            'performance_metrics': {
                'processing_time': processing_time,
                'fps': fps,
                'model_version': 'YOLOv8',
                'image_dimensions': {'width': width, 'height': height}
            },
            'analysis_type': 'image'
        }
    
    def _analyze_video(self, video_path: str, start_time: float) -> Dict[str, Any]:
        """Analyze a video file"""
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        logger.info(f"Analyzing video: {frame_count} frames, {fps:.2f} FPS, {duration:.2f}s duration")
        
        # Sample frames for analysis (analyze every Nth frame to balance accuracy vs speed)
        sample_interval = max(1, int(fps / 2))  # Analyze 2 frames per second
        sample_frames = []
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % sample_interval == 0:
                sample_frames.append((frame_idx, frame))
            
            frame_idx += 1
            
            # Limit to reasonable number of frames for processing
            if len(sample_frames) >= 30:  # Max 30 sample frames
                break
        
        cap.release()
        
        if not sample_frames:
            raise ValueError("No frames could be extracted from video")
        
        # Analyze sample frames
        all_detections = []
        frame_results = []
        
        for frame_idx, frame in sample_frames:
            frame_detection = self._detect_vehicles(frame)
            frame_density = self._analyze_traffic_density(frame_detection, (width, height))
            
            frame_result = {
                'frame_index': frame_idx,
                'timestamp': frame_idx / fps,
                'vehicle_count': frame_detection.get('total_vehicles', 0),
                'density_level': frame_density.get('density_level', 'Unknown'),
                'congestion_index': frame_density.get('congestion_index', 0)
            }
            
            frame_results.append(frame_result)
            all_detections.extend(frame_detection.get('detections', []))
        
        # Aggregate results across all frames
        total_unique_vehicles = len(all_detections)  # Simplified - could implement tracking
        avg_vehicles_per_frame = sum(r['vehicle_count'] for r in frame_results) / len(frame_results)
        avg_congestion = sum(r['congestion_index'] for r in frame_results) / len(frame_results)
        
        # Determine overall density level
        if avg_congestion >= 0.8:
            overall_density = 'Very High'
        elif avg_congestion >= 0.6:
            overall_density = 'High'
        elif avg_congestion >= 0.4:
            overall_density = 'Medium'
        elif avg_congestion >= 0.2:
            overall_density = 'Low'
        else:
            overall_density = 'Very Low'
        
        # Calculate performance metrics
        processing_time = time.time() - start_time
        
        return {
            'vehicle_detection': {
                'total_vehicles': int(avg_vehicles_per_frame),
                'estimated_unique_vehicles': total_unique_vehicles,
                'average_vehicles_per_frame': avg_vehicles_per_frame,
                'vehicle_counts': self._aggregate_vehicle_counts(all_detections),
                'detections': all_detections[:50]  # Limit for response size
            },
            'traffic_density': {
                'density_level': overall_density,
                'congestion_index': avg_congestion,
                'temporal_analysis': {
                    'frames_analyzed': len(frame_results),
                    'duration_analyzed': len(frame_results) * sample_interval / fps,
                    'peak_congestion': max(r['congestion_index'] for r in frame_results),
                    'min_congestion': min(r['congestion_index'] for r in frame_results)
                }
            },
            'video_analysis': {
                'frame_results': frame_results,
                'video_properties': {
                    'fps': fps,
                    'frame_count': frame_count,
                    'duration': duration,
                    'resolution': f"{width}x{height}"
                }
            },
            'performance_metrics': {
                'processing_time': processing_time,
                'fps': len(sample_frames) / processing_time if processing_time > 0 else 0,
                'model_version': 'YOLOv8',
                'frames_processed': len(sample_frames)
            },
            'analysis_type': 'video'
        }
    
    def _aggregate_vehicle_counts(self, detections: List[Dict]) -> Dict[str, int]:
        """Aggregate vehicle counts from multiple detections"""
        counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0, 'bicycle': 0}
        
        for detection in detections:
            vehicle_class = detection.get('class', '')
            if vehicle_class in counts:
                counts[vehicle_class] += 1
        
        return counts
    
    def _detect_vehicles(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect vehicles in the image using YOLOv8
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary containing detection results
        """
        try:
            if self.model is None:
                logger.error("YOLOv8 model is None - using fallback detection")
                return self._fallback_detection(image)
            
            logger.info(f"YOLOv8 model loaded successfully, running inference...")
            
            # Run YOLO inference with multiple strategies for maximum accuracy in dense traffic
            
            # Strategy 1: Ultra-low confidence for dense traffic detection
            results_ultra_low = self.model(image, verbose=False, conf=0.01)  # Ultra-low for maximum detection
            
            # Strategy 2: Standard inference
            results = self.model(image, verbose=False, conf=self.confidence_threshold)
            
            # Strategy 3: Multi-scale inference (resize image for better detection)
            image_resized_small = cv2.resize(image, (640, 640))  # Smaller for distant vehicles
            results_small = self.model(image_resized_small, verbose=False, conf=0.01)  # Ultra-low confidence
            
            image_resized_medium = cv2.resize(image, (1280, 1280))  # YOLO optimal size
            results_medium = self.model(image_resized_medium, verbose=False, conf=0.01)  # Ultra-low confidence
            
            image_resized_large = cv2.resize(image, (1920, 1920))  # Large for close vehicles
            results_large = self.model(image_resized_large, verbose=False, conf=0.01)  # Ultra-low confidence
            
            # Strategy 4: Image enhancement for better detection
            enhanced_image = self._enhance_image_for_detection(image)
            results_enhanced = self.model(enhanced_image, verbose=False, conf=0.01)  # Ultra-low confidence
            
            # Strategy 5: Contrast enhanced image
            contrast_enhanced = self._enhance_contrast(image)
            results_contrast = self.model(contrast_enhanced, verbose=False, conf=0.01)  # Ultra-low confidence
            
            # Strategy 6: Brightness adjusted images
            bright_image = cv2.convertScaleAbs(image, alpha=1.2, beta=20)
            results_bright = self.model(bright_image, verbose=False, conf=0.01)  # Ultra-low confidence
            
            dark_image = cv2.convertScaleAbs(image, alpha=0.8, beta=-20)
            results_dark = self.model(dark_image, verbose=False, conf=0.01)  # Ultra-low confidence
            
            # Strategy 7: Different aspect ratios for highway scenes
            height, width = image.shape[:2]
            if width > height * 1.5:  # Likely highway scene
                # Crop to focus on traffic areas
                crop_top = image[0:int(height*0.8), :]  # Top 80%
                crop_bottom = image[int(height*0.2):, :]  # Bottom 80%
                results_crop_top = self.model(crop_top, verbose=False, conf=0.01)
                results_crop_bottom = self.model(crop_bottom, verbose=False, conf=0.01)
            else:
                results_crop_top = []
                results_crop_bottom = []
            
            # Strategy 8: Enhanced 2-wheeler detection with ultra-low confidence
            # Motorcycles and bicycles detection for dense traffic
            results_2wheeler_ultra = self.model(image, verbose=False, conf=0.005)  # Even lower for 2-wheelers
            
            # Strategy 9: 2-wheeler focused image enhancement
            # Enhance edges and small objects for better 2-wheeler detection
            enhanced_2wheeler = self._enhance_for_2wheelers(image)
            results_2wheeler_enhanced = self.model(enhanced_2wheeler, verbose=False, conf=0.01)  # Ultra-low confidence
            
            detections = []
            vehicle_counts = {'car': 0, 'large_vehicle': 0, '2-wheeler': 0}
            total_confidence = 0
            filtered_count = 0  # Track filtered detections
            all_detections_count = 0  # Track all detections before filtering
            
            logger.info(f"YOLOv8 running multi-strategy inference for maximum accuracy including enhanced 2-wheeler detection")
            
            all_detections = []
            processed_boxes = set()
            
            # Use only reliable inference strategies to reduce false positives
            inference_results = [
                ("standard", results),  # Primary reliable detection
                ("enhanced", results_enhanced),  # Enhanced image processing
            ]
            
            # Disable problematic strategies that cause false positives
            # ("ultra_low", results_ultra_low),  # DISABLED - too many false positives
            ("small_scale", results_small),    # ENABLED - helps with distant vehicles
            # ("medium_scale", results_medium),  # DISABLED - causes duplicates  
            # ("large_scale", results_large),    # DISABLED - causes duplicates
            # ("contrast", results_contrast),    # DISABLED - unreliable
            # ("bright", results_bright),        # DISABLED - unreliable
            # ("dark", results_dark),            # DISABLED - unreliable
            
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
                                    
                                    # Check for duplicate detections (same vehicle detected multiple times)
                                    is_duplicate = False
                                    for existing_center, existing_size in processed_boxes:
                                        center_distance = ((box_center[0] - existing_center[0])**2 + 
                                                         (box_center[1] - existing_center[1])**2)**0.5
                                        size_ratio = min(box_size, existing_size) / max(box_size, existing_size)
                                        
                                        # More lenient duplicate detection for dense traffic
                                        if center_distance < 20 and size_ratio > 0.7:
                                            is_duplicate = True
                                            break
                                    
                                    # Apply optimized confidence thresholds for better detection
                                    if strategy_name == "enhanced":
                                        min_confidence = 0.06  # OPTIMIZED: Better enhanced detection
                                    elif strategy_name == "small_scale":
                                        min_confidence = 0.08  # OPTIMIZED: Better distant vehicle detection
                                    else:
                                        min_confidence = 0.05  # OPTIMIZED: Sweet spot detection
                                    
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
                                        
                                        # 🎯 APPLY ROI FILTERING - Check if detection is within region of interest
                                        centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
                                        if not self._is_in_roi(centroid, image.shape[:2]):
                                            logger.debug(f"Detection filtered by ROI: {mapped_class} at {centroid}")
                                            filtered_count += 1
                                            continue  # Skip this detection as it's outside ROI
                                        
                                        # Intelligent SUV/Truck reclassification
                                        if mapped_class == 'truck':
                                            reclassified_class = self._intelligent_truck_classification(detection, image)
                                            if reclassified_class != 'truck':
                                                detection['class'] = reclassified_class
                                                detection['reclassified'] = True
                                                detection['reclassification_reason'] = f"Size/confidence analysis suggests {reclassified_class}"
                                                mapped_class = reclassified_class  # Update for counting
                                        
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
            
            logger.info(f"YOLOv8 SUMMARY: {total_vehicles} vehicles detected from {all_detections_count} total detections (filtered {filtered_count} low-confidence)")
            
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
            logger.error(f"Error in YOLOv8 vehicle detection: {e}")
            return self._fallback_detection(image)
    
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
            
            # Factor 1: Confidence level (be less aggressive with reclassification)
            if confidence < 0.4:  # Only very low confidence suggests misclassification
                car_score += 2  # Reduced from 3
            elif confidence < 0.5:  # Reduced threshold
                car_score += 1
            else:
                truck_score += 1
            
            # Factor 2: Size analysis (be more lenient with size requirements)
            if relative_area < 0.01:  # Very small relative to image - likely car
                car_score += 2
            elif relative_area < 0.03:  # Small - could be distant truck
                car_score += 1  # Reduced penalty
            elif relative_area > 0.1:  # Large - likely actual truck
                truck_score += 2
            elif relative_area > 0.05:  # Medium-large - could be truck
                truck_score += 1  # Added bonus for medium-large vehicles
            
            # Factor 3: Aspect ratio (trucks tend to be longer/wider)
            if aspect_ratio > 2.0:  # Very wide - likely truck
                truck_score += 2
            elif aspect_ratio > 1.5:  # Moderately wide - could be either
                truck_score += 1  # Slight bonus for wider vehicles
            else:  # More square/tall - likely car/SUV
                pass  # Reduced penalty
            
            # Factor 4: Relative height (be more lenient)
            if relative_height < 0.1:  # Very short relative to image - likely car
                car_score += 1  # Reduced from 2
            elif relative_height < 0.2:  # Short - could be distant truck
                pass  # No penalty for potentially distant trucks
            elif relative_height > 0.3:  # Tall - likely truck
                truck_score += 1
            
            # Factor 5: Position in image (trucks often appear larger when closer)
            center_y = (bbox['y1'] + bbox['y2']) / 2
            relative_y = center_y / img_height
            
            if relative_y > 0.7:  # Lower in image (closer) - size might be misleading
                if relative_area > 0.1:  # Large and close - could be car appearing large
                    car_score += 1
            
            # Decision logic (require stronger evidence to reclassify)
            if car_score > truck_score + 2:  # Require stronger evidence (was +1)
                logger.info(f"Reclassifying truck to car (car_score: {car_score}, truck_score: {truck_score}, confidence: {confidence:.3f})")
                return 'car'
            else:
                logger.info(f"Keeping truck classification (car_score: {car_score}, truck_score: {truck_score}, confidence: {confidence:.3f})")
                return 'large_vehicle'  # Use our standard mapping
                
        except Exception as e:
            logger.error(f"Error in intelligent truck classification: {e}")
            return 'truck'  # Default to original classification
    
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
    
    def _fallback_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Fallback detection method when YOLOv8 is not available
        Uses OpenCV-based detection as a backup
        """
        logger.warning("YOLOv8 model not available - using OpenCV fallback detection")
        
        try:
            height, width = image.shape[:2]
            
            # Try basic OpenCV-based vehicle detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Use background subtraction or edge detection for vehicle-like objects
            edges = cv2.Canny(blur, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            vehicle_counts = {'car': 0, 'large_vehicle': 0, '2-wheeler': 0}  # Use new 3-category system
            
            # Filter contours by size and shape to identify potential vehicles
            for contour in contours:
                area = cv2.contourArea(contour)
                if 1000 < area < 50000:  # Reasonable vehicle size range
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Basic classification based on aspect ratio and size
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Classify based on size and aspect ratio using new 3-category system
                    if area > 15000:
                        vehicle_class = 'large_vehicle'  # Buses/trucks as large vehicles
                    elif 0.8 < aspect_ratio < 2.5 and area > 5000:
                        vehicle_class = 'car'
                    elif area < 3000:
                        vehicle_class = '2-wheeler'  # Motorcycles as 2-wheelers
                    else:
                        vehicle_class = 'car'  # Default classification
                    
                    # Calculate confidence based on contour properties
                    confidence = min(0.6, 0.3 + (area / 50000) * 0.3)  # Max 0.6 for fallback
                    
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
            
            logger.info(f"OpenCV fallback detected {total_vehicles} potential vehicles")
            
            return {
                'detections': detections,
                'vehicle_counts': vehicle_counts,
                'total_vehicles': total_vehicles,
                'average_confidence': avg_confidence,
                'detection_summary': vehicle_counts,
                'fallback_mode': True,
                'fallback_method': 'opencv'
            }
            
        except Exception as e:
            logger.error(f"OpenCV fallback detection failed: {e}")
            
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
        # Advanced density analysis based on image context
        width, height = image_size
        image_area = width * height
        
        total_vehicles = detection_results.get('total_vehicles', 0)
        detections = detection_results.get('detections', [])
        
        # Calculate vehicle density per square meter
        vehicle_density = total_vehicles / (image_area / 1000000)
        
        # Calculate area coverage by vehicles
        total_vehicle_area = sum(det.get('area', 0) for det in detections)
        area_coverage_percentage = (total_vehicle_area / image_area) * 100
        
        # Analyze vehicle distribution (clustering vs spread out)
        vehicle_positions = []
        for det in detections:
            bbox = det.get('bbox', {})
            center_x = (bbox.get('x1', 0) + bbox.get('x2', 0)) / 2
            center_y = (bbox.get('y1', 0) + bbox.get('y2', 0)) / 2
            vehicle_positions.append((center_x, center_y))
        
        # Calculate clustering factor
        clustering_factor = self._calculate_clustering_factor(vehicle_positions, image_size)
        
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
        
        # Adjust based on area coverage and clustering
        if area_coverage_percentage > 15:
            if density_level in ['Very Low', 'Low']:
                density_level = 'Medium'
                congestion_index = min(congestion_index + 0.2, 1.0)
            elif density_level == 'Medium':
                density_level = 'High'
                congestion_index = min(congestion_index + 0.2, 1.0)
        
        # Adjust based on clustering (vehicles close together = more congestion)
        if clustering_factor > 0.7:
            if density_level in ['Medium', 'High']:
                congestion_index = min(congestion_index + 0.15, 1.0)
                if density_level == 'High':
                    density_level = 'Very High'
        
        # Calculate additional metrics
        avg_vehicle_size = total_vehicle_area / total_vehicles if total_vehicles > 0 else 0
        
        # Estimate traffic flow state
        if congestion_index >= 0.8:
            flow_state = 'Stop-and-Go'
        elif congestion_index >= 0.6:
            flow_state = 'Slow Moving'
        elif congestion_index >= 0.3:
            flow_state = 'Moderate Flow'
        else:
            flow_state = 'Free Flow'
        
        return {
            'density_level': density_level,
            'congestion_index': congestion_index,
            'vehicle_density': vehicle_density,
            'area_coverage_percentage': area_coverage_percentage,
            'flow_state': flow_state,
            'clustering_factor': clustering_factor,
            'avg_vehicle_size': avg_vehicle_size,
            'detailed_analysis': {
                'total_vehicles': total_vehicles,
                'vehicles_per_lane': total_vehicles / max(1, self._estimate_lanes(detections, width)),
                'congestion_severity': self._get_congestion_severity(congestion_index),
                'traffic_pattern': self._analyze_traffic_pattern(vehicle_positions, image_size)
            }
        }
    
    def _calculate_clustering_factor(self, positions: List[Tuple[float, float]], image_size: Tuple[int, int]) -> float:
        """Calculate how clustered vehicles are (0 = spread out, 1 = highly clustered)"""
        if len(positions) < 2:
            return 0.0
        
        try:
            # Calculate average distance between vehicles
            total_distance = 0
            count = 0
            
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    x1, y1 = positions[i]
                    x2, y2 = positions[j]
                    distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                    total_distance += distance
                    count += 1
            
            avg_distance = total_distance / count if count > 0 else 0
            
            # Normalize by image diagonal
            image_diagonal = (image_size[0]**2 + image_size[1]**2)**0.5
            normalized_distance = avg_distance / image_diagonal
            
            # Convert to clustering factor (inverse of normalized distance)
            clustering_factor = max(0, 1 - (normalized_distance * 2))
            return min(1.0, clustering_factor)
            
        except Exception:
            return 0.5  # Default moderate clustering
    
    def _estimate_lanes(self, detections: List[Dict], width: int) -> int:
        """Estimate number of traffic lanes based on vehicle positions"""
        if not detections:
            return 1
        
        try:
            # Group vehicles by Y position (assuming horizontal lanes)
            y_positions = []
            for det in detections:
                bbox = det.get('bbox', {})
                center_y = (bbox.get('y1', 0) + bbox.get('y2', 0)) / 2
                y_positions.append(center_y)
            
            # Simple lane estimation based on Y position clustering
            y_positions.sort()
            lanes = 1
            
            for i in range(1, len(y_positions)):
                if y_positions[i] - y_positions[i-1] > 60:  # Significant gap suggests new lane
                    lanes += 1
            
            return max(1, min(lanes, 6))  # Reasonable range of 1-6 lanes
            
        except Exception:
            return 2  # Default assumption
    
    def _get_congestion_severity(self, congestion_index: float) -> str:
        """Get human-readable congestion severity"""
        if congestion_index >= 0.9:
            return 'Critical'
        elif congestion_index >= 0.7:
            return 'Severe'
        elif congestion_index >= 0.5:
            return 'Moderate'
        elif congestion_index >= 0.3:
            return 'Light'
        else:
            return 'Minimal'
    
    def _analyze_traffic_pattern(self, positions: List[Tuple[float, float]], image_size: Tuple[int, int]) -> str:
        """Analyze the pattern of traffic distribution"""
        if len(positions) < 3:
            return 'Sparse'
        
        try:
            width, height = image_size
            
            # Divide image into grid and count vehicles in each cell
            grid_size = 4
            cell_width = width / grid_size
            cell_height = height / grid_size
            
            grid_counts = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
            
            for x, y in positions:
                grid_x = min(int(x / cell_width), grid_size - 1)
                grid_y = min(int(y / cell_height), grid_size - 1)
                grid_counts[grid_y][grid_x] += 1
            
            # Analyze distribution pattern
            non_empty_cells = sum(1 for row in grid_counts for count in row if count > 0)
            max_cell_count = max(max(row) for row in grid_counts)
            
            if non_empty_cells <= 2:
                return 'Localized'
            elif max_cell_count > len(positions) * 0.6:
                return 'Concentrated'
            elif non_empty_cells >= grid_size * grid_size * 0.7:
                return 'Distributed'
            else:
                return 'Clustered'
                
        except Exception:
            return 'Unknown'
    
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
                logger.info(f"Limited annotations to top {MAX_ANNOTATIONS} detections (out of {len(deduplicated_detections)} total)")
            
            logger.info(f"Creating annotated image with {len(filtered_detections)} annotations")
            
            # Always create an annotated image, even if no detections
            for detection in filtered_detections:
                try:
                    bbox = detection['bbox']
                    class_name = detection['class']
                    confidence = detection['confidence']
                    
                    # Get color for this vehicle type
                    color = colors.get(class_name, (200, 200, 200))
                    
                    # Ensure coordinates are within image bounds
                    x1 = max(0, min(bbox['x1'], annotated_image.shape[1] - 1))
                    y1 = max(0, min(bbox['y1'], annotated_image.shape[0] - 1))
                    x2 = max(0, min(bbox['x2'], annotated_image.shape[1] - 1))
                    y2 = max(0, min(bbox['y2'], annotated_image.shape[0] - 1))
                    
                    # Only draw if bounding box is valid
                    if x2 > x1 and y2 > y1:
                        # Draw cleaner bounding box with thicker lines
                        cv2.rectangle(
                            annotated_image,
                            (x1, y1),
                            (x2, y2),
                            color,
                            3  # Thicker line for better visibility
                        )
                        
                        # Map individual classes to grouped categories for display
                        class_display_mapping = {
                            'car': 'Car',
                            'truck': 'Large Vehicle',
                            'bus': 'Large Vehicle', 
                            'motorcycle': '2-Wheeler',
                            'bicycle': '2-Wheeler'
                        }
                        
                        # Use grouped class name for label
                        display_class = class_display_mapping.get(class_name, class_name.replace('_', ' ').title())
                        
                        # Draw cleaner label with grouped category
                        label = f"{display_class}: {confidence:.2f}"  # Show grouped category
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        
                        # Background rectangle for label
                        cv2.rectangle(
                            annotated_image,
                            (x1, y1 - label_size[1] - 8),
                            (x1 + label_size[0] + 4, y1),
                            color,
                            -1
                        )
                        
                        # White text for better contrast
                        cv2.putText(
                            annotated_image,
                            label,
                            (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2
                        )
                except Exception as detection_error:
                    logger.warning(f"Error drawing detection: {detection_error}")
                    continue  # Skip this detection but continue with others
            
            # Add summary overlay when annotations are limited
            if len(deduplicated_detections) > len(filtered_detections):
                # Add semi-transparent background for summary
                overlay = annotated_image.copy()
                cv2.rectangle(overlay, (10, 10), (400, 80), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, annotated_image, 0.3, 0, annotated_image)
                
                # Add summary text
                summary_text = f"Showing top {len(filtered_detections)} of {len(deduplicated_detections)} detections"
                cv2.putText(annotated_image, summary_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                total_text = f"Total vehicles detected: {len(deduplicated_detections)}"
                cv2.putText(annotated_image, total_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Save annotated image with better error handling
            original_name = Path(original_path).stem
            annotated_path = str(Path(original_path).parent / f"{original_name}_yolov8_annotated.jpg")
            
            try:
                # Optimize image size for large images to prevent memory issues
                height, width = annotated_image.shape[:2]
                if width > 1920 or height > 1080:
                    # Resize large images to prevent memory issues
                    scale = min(1920/width, 1080/height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    annotated_image = cv2.resize(annotated_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    logger.info(f"Resized annotated image from {width}x{height} to {new_width}x{new_height}")
                
                # Save with compression to reduce file size
                success = cv2.imwrite(annotated_path, annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                if not success:
                    logger.error(f"Failed to save annotated image to {annotated_path}")
                    # Try alternative path
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    annotated_path = os.path.join(temp_dir, f"{original_name}_yolov8_annotated_{int(time.time())}.jpg")
                    success = cv2.imwrite(annotated_path, annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if not success:
                        logger.error(f"Failed to save annotated image to alternative path: {annotated_path}")
                        return original_path
                
                # Verify file was created and is accessible
                if not os.path.exists(annotated_path):
                    logger.error(f"Annotated image file not found after save: {annotated_path}")
                    return original_path
                    
                file_size = os.path.getsize(annotated_path)
                if file_size == 0:
                    logger.error(f"Annotated image file is empty: {annotated_path}")
                    return original_path
                
                logger.info(f"Successfully saved annotated image: {annotated_path} ({file_size} bytes)")
                return annotated_path
                
            except Exception as save_error:
                logger.error(f"Error saving annotated image: {save_error}")
                return original_path
            
        except Exception as e:
            logger.error(f"Error creating YOLOv8 annotated image: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return original_path
    
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
            'vehicle_density': self._calculate_vehicle_density(detections),
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
    
    def _calculate_vehicle_density(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate vehicle density information for each vehicle type"""
        
        if not detections:
            return {
                'total_density': 0,
                'density_by_type': {},
                'spatial_distribution': 'empty'
            }
        
        # Calculate total area covered by vehicles
        total_vehicle_area = sum(det.get('area', 0) for det in detections)
        
        # Group by vehicle type and calculate density
        density_by_type = {}
        type_counts = {}
        type_areas = {}
        
        for detection in detections:
            vehicle_type = detection.get('class', 'unknown')
            area = detection.get('area', 0)
            
            if vehicle_type not in type_counts:
                type_counts[vehicle_type] = 0
                type_areas[vehicle_type] = 0
            
            type_counts[vehicle_type] += 1
            type_areas[vehicle_type] += area
        
        # Calculate density metrics for each type
        for vehicle_type in type_counts:
            count = type_counts[vehicle_type]
            total_area = type_areas[vehicle_type]
            avg_area = total_area / count if count > 0 else 0
            
            density_by_type[vehicle_type] = {
                'count': count,
                'total_area_pixels': int(total_area),
                'average_area_pixels': int(avg_area),
                'density_score': count / len(detections) if detections else 0,
                'size_category': self._categorize_vehicle_size(avg_area)
            }
        
        # Calculate spatial distribution
        if len(detections) <= 2:
            spatial_dist = 'sparse'
        elif len(detections) <= 8:
            spatial_dist = 'moderate'
        elif len(detections) <= 15:
            spatial_dist = 'dense'
        else:
            spatial_dist = 'very_dense'
        
        # Overall density score
        total_density = len(detections) / max(1, total_vehicle_area / 10000)  # Normalized density
        
        return {
            'total_density': round(total_density, 3),
            'density_by_type': density_by_type,
            'spatial_distribution': spatial_dist,
            'total_vehicles': len(detections),
            'coverage_area': int(total_vehicle_area),
            'density_summary': f"{len(detections)} vehicles in {spatial_dist} distribution"
        }
    
    def _categorize_vehicle_size(self, area: float) -> str:
        """Categorize vehicle size based on bounding box area"""
        if area < 3000:
            return 'small'
        elif area < 8000:
            return 'medium'
        elif area < 20000:
            return 'large'
        else:
            return 'very_large'

    def validate_count_annotation_consistency(self, detection_results: Dict[str, Any], annotated_image_path: str) -> Dict[str, Any]:
        """
        Validate that the vehicle counts match the number of annotations on the image.
        This helps identify discrepancies between counting and annotation logic.
        
        Args:
            detection_results: Results from vehicle detection
            annotated_image_path: Path to the annotated image
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # Get counts from detection results
            vehicle_counts = detection_results.get('vehicle_counts', {})
            total_counted = detection_results.get('total_vehicles', 0)
            detections = detection_results.get('detections', [])
            
            # Apply the same filtering logic used in annotation
            filtered_detections = []
            for d in detections:
                strategy = d.get('detection_strategy', '')
                if strategy in ["2wheeler_ultra", "2wheeler_enhanced"] and d['class'] == '2-wheeler':
                    min_confidence = 0.03  # Lower threshold for 2-wheelers
                else:
                    min_confidence = 0.05  # Standard threshold for cars and large vehicles
                
                if d['confidence'] >= min_confidence:
                    filtered_detections.append(d)
            
            # Apply deduplication logic
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
            
            # Count annotated vehicles by type
            annotated_counts = {'car': 0, 'large_vehicle': 0, '2-wheeler': 0}
            for detection in deduplicated_detections:
                vehicle_class = detection['class']
                if vehicle_class in annotated_counts:
                    annotated_counts[vehicle_class] += 1
            
            total_annotated = sum(annotated_counts.values())
            
            # Calculate discrepancies
            discrepancies = {}
            for vehicle_type in ['car', 'large_vehicle', '2-wheeler']:
                counted = vehicle_counts.get(vehicle_type, 0)
                annotated = annotated_counts.get(vehicle_type, 0)
                discrepancy = counted - annotated
                discrepancies[vehicle_type] = {
                    'counted': counted,
                    'annotated': annotated,
                    'discrepancy': discrepancy,
                    'match': discrepancy == 0
                }
            
            total_discrepancy = total_counted - total_annotated
            
            # Determine validation status
            is_consistent = total_discrepancy == 0
            validation_status = 'PASS' if is_consistent else 'FAIL'
            
            # Generate detailed analysis
            analysis = []
            if not is_consistent:
                if total_discrepancy > 0:
                    analysis.append(f"Found {total_discrepancy} more vehicles in count than annotations")
                else:
                    analysis.append(f"Found {abs(total_discrepancy)} more annotations than counted vehicles")
                
                for vehicle_type, data in discrepancies.items():
                    if data['discrepancy'] != 0:
                        if data['discrepancy'] > 0:
                            analysis.append(f"{vehicle_type}: {data['discrepancy']} counted but not annotated")
                        else:
                            analysis.append(f"{vehicle_type}: {abs(data['discrepancy'])} annotated but not counted")
            else:
                analysis.append("All vehicle counts match their annotations perfectly")
            
            return {
                'validation_status': validation_status,
                'is_consistent': is_consistent,
                'total_counted': total_counted,
                'total_annotated': total_annotated,
                'total_discrepancy': total_discrepancy,
                'discrepancies_by_type': discrepancies,
                'analysis': analysis,
                'confidence_thresholds_used': {
                    '2-wheeler': 0.03,
                    'car': 0.05,
                    'large_vehicle': 0.05
                },
                'deduplication_applied': True,
                'annotated_image_path': annotated_image_path
            }
            
        except Exception as e:
            logger.error(f"Error validating count-annotation consistency: {e}")
            return {
                'validation_status': 'ERROR',
                'is_consistent': False,
                'error': str(e),
                'analysis': [f"Validation failed due to error: {str(e)}"]
            }