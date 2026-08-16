"""
Advanced YOLO Traffic Analysis Service with State-of-the-Art Models
Uses YOLOv8x, YOLOv9, YOLOv10 and ensemble methods for maximum accuracy
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class AdvancedYOLOTrafficAnalyzer:
    """
    Advanced traffic analysis using state-of-the-art YOLO models
    Implements ensemble methods and advanced post-processing for maximum accuracy
    """
    
    def __init__(self, device: str = 'auto', confidence_threshold: float = 0.2):  # Increased from 0.001
        """
        Initialize the advanced ensemble analyzer with multiple YOLO models for balanced accuracy
        
        Args:
            device: Device to run inference on ('cpu', 'cuda', or 'auto')
            confidence_threshold: Base confidence threshold (0.2 for reliable ensemble detection)
        """
        self.device = self._setup_device(device)
        self.confidence_threshold = confidence_threshold
        self.models = {}
        self.class_names = self._get_coco_classes()
        
        # Advanced ensemble configuration
        self.ensemble_voting_threshold = 0.3  # Require 30% of models to agree
        self.max_detections_per_model = 1000  # Maximum detections per model
        self.iou_threshold = 0.25  # Lower IoU for better ensemble consensus
        self.confidence_boost_factor = 1.2  # Boost confidence for ensemble consensus
        self.advanced_nms = True  # Use advanced non-maximum suppression
        
        # Standardized vehicle classes same as other models
        self.vehicle_classes = ['car', 'large_vehicle', '2-wheeler']
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
        
        # Load advanced models
        self._load_advanced_models()
        
        logger.info(f"Advanced YOLO analyzer initialized with {len(self.models)} models on {self.device}")
    
    def _setup_device(self, device: str) -> str:
        """Setup optimal device for inference"""
        try:
            import torch
            
            if device == 'auto':
                if torch.cuda.is_available():
                    device = 'cuda'
                    logger.info("CUDA available - using GPU acceleration")
                else:
                    device = 'cpu'
                    logger.info("CUDA not available - using CPU")
            
            return device
        except ImportError:
            logger.warning("PyTorch not available, using CPU")
            return 'cpu'
    
    def _get_coco_classes(self) -> List[str]:
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
    
    def _load_advanced_models(self):
        """Load multiple advanced YOLO models for ensemble detection"""
        try:
            from ultralytics import YOLO
            
            # Model configurations optimized for dense traffic detection
            model_configs = [
                {
                    'name': 'yolov8s',
                    'model_file': os.path.join('backend', 'models', 'yolov8s.pt'),
                    'description': 'YOLOv8 Small - Fast and reliable',
                    'confidence': 0.01,  # Ultra-low for dense traffic
                    'weight': 0.4  # Higher weight for proven model
                },
                {
                    'name': 'yolo11s',
                    'model_file': os.path.join('backend', 'models', 'yolo11s.pt'),
                    'description': 'YOLOv11 Small - Enhanced accuracy',
                    'confidence': 0.01,  # Ultra-low for dense traffic
                    'weight': 0.3
                },
                {
                    'name': 'yolo12s',
                    'model_file': os.path.join('backend', 'models', 'yolo12s.pt'),
                    'description': 'YOLOv12 Small - Latest model',
                    'confidence': 0.01,  # Ultra-low for dense traffic
                    'weight': 0.3
                }
            ]
            
            # Load models (only use the three available models)
            loaded_models = 0
            for config in model_configs:
                try:
                    model = YOLO(config['model_file'])
                    if hasattr(model, 'to') and self.device != 'cpu':
                        model.to(self.device)
                    
                    self.models[config['name']] = {
                        'model': model,
                        'confidence': config['confidence'],
                        'weight': config['weight'],
                        'description': config['description']
                    }
                    loaded_models += 1
                    logger.info(f"Loaded {config['name']}: {config['description']}")
                    
                except Exception as e:
                    logger.warning(f"Could not load {config['name']}: {e}")
            
            if loaded_models == 0:
                raise Exception("No YOLO models could be loaded")
            
            # Normalize weights
            total_weight = sum(model_info['weight'] for model_info in self.models.values())
            for model_info in self.models.values():
                model_info['weight'] = model_info['weight'] / total_weight
            
            logger.info(f"Successfully loaded {loaded_models} advanced YOLO models")
            
        except ImportError:
            logger.error("Ultralytics not installed. Install with: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Failed to load advanced YOLO models: {e}")
            raise
    
    def analyze_traffic_scene(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze traffic scene using ensemble of advanced YOLO models
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        start_time = time.time()
        
        try:
            # Load and validate image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            height, width = image.shape[:2]
            logger.info(f"Analyzing image: {width}x{height} pixels")
            
            # Run ensemble detection
            ensemble_results = self._run_ensemble_detection(image)
            
            # Advanced post-processing
            processed_results = self._advanced_post_processing(ensemble_results, (width, height))
            
            # Traffic density analysis
            density_results = self._analyze_traffic_density_advanced(processed_results, (width, height))
            
            # Performance metrics
            processing_time = time.time() - start_time
            
            # Create comprehensive results
            results = {
                'vehicle_detection': {
                    'detections': processed_results['final_detections'],
                    'vehicle_counts': processed_results['vehicle_counts'],
                    'total_vehicles': processed_results['total_vehicles'],
                    'average_confidence': processed_results['average_confidence'],
                    'detection_summary': processed_results['detection_summary'],
                    'vehicle_breakdown': processed_results['vehicle_breakdown'],
                    'ensemble_info': processed_results['ensemble_info']
                },
                'traffic_density': density_results,
                'performance_metrics': {
                    'processing_time': processing_time,
                    'fps': 1.0 / processing_time if processing_time > 0 else 0,
                    'model_version': 'Advanced-YOLO-Ensemble',
                    'models_used': list(self.models.keys()),
                    'image_dimensions': {'width': width, 'height': height},
                    'device_used': self.device
                },
                'analysis_type': 'image',
                'accuracy_level': 'maximum'
            }
            
            logger.info(f"Advanced analysis completed: {processed_results['total_vehicles']} vehicles detected in {processing_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error in advanced traffic analysis: {e}")
            return {
                'error': str(e),
                'vehicle_detection': {},
                'traffic_density': {},
                'performance_metrics': {
                    'processing_time': time.time() - start_time,
                    'fps': 0,
                    'model_version': 'Advanced-YOLO-Ensemble',
                    'error': True
                }
            }
    
    def _run_ensemble_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Run ensemble detection using all available models"""
        
        logger.info(f"Running ensemble detection with {len(self.models)} models")
        
        all_detections = []
        model_results = {}
        
        # Run all models in parallel for speed
        with ThreadPoolExecutor(max_workers=len(self.models)) as executor:
            future_to_model = {
                executor.submit(self._run_single_model_detection, model_name, model_info, image): model_name
                for model_name, model_info in self.models.items()
            }
            
            for future in as_completed(future_to_model):
                model_name = future_to_model[future]
                try:
                    detections = future.result()
                    model_results[model_name] = detections
                    
                    # Add model weight to each detection
                    model_weight = self.models[model_name]['weight']
                    for detection in detections:
                        detection['model_weight'] = model_weight
                        detection['source_model'] = model_name
                    
                    all_detections.extend(detections)
                    logger.info(f"{model_name}: {len(detections)} detections")
                    
                except Exception as e:
                    logger.error(f"Model {model_name} failed: {e}")
                    model_results[model_name] = []
        
        return {
            'all_detections': all_detections,
            'model_results': model_results,
            'total_raw_detections': len(all_detections)
        }
    
    def _run_single_model_detection(self, model_name: str, model_info: Dict, image: np.ndarray) -> List[Dict]:
        """Run detection on a single model with multiple strategies"""
        
        model = model_info['model']
        confidence = model_info['confidence']
        
        detections = []
        
        try:
            # Strategy 1: Standard detection
            results = model(image, verbose=False, conf=confidence)
            
            # Strategy 2: Multi-scale detection
            scales = [640, 832, 1024, 1280]  # Different input sizes
            for scale in scales:
                try:
                    resized_image = cv2.resize(image, (scale, scale))
                    scale_results = model(resized_image, verbose=False, conf=max(0.005, confidence * 0.5))  # Much lower confidence for scaled detection
                    
                    # Scale coordinates back
                    scale_factor_x = image.shape[1] / scale
                    scale_factor_y = image.shape[0] / scale
                    
                    for result in scale_results:
                        if result.boxes is not None:
                            for box in result.boxes:
                                class_id = int(box.cls[0])
                                conf = float(box.conf[0])
                                
                                if class_id < len(self.class_names):
                                    class_name = self.class_names[class_id]
                                    
                                    # Check if it's a vehicle
                                    vehicle_type = self._classify_vehicle(class_name)
                                    if vehicle_type:
                                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                                        
                                        # Scale back to original image size
                                        x1, x2 = x1 * scale_factor_x, x2 * scale_factor_x
                                        y1, y2 = y1 * scale_factor_y, y2 * scale_factor_y
                                        
                                        detection = {
                                            'class': vehicle_type,
                                            'original_class': class_name,
                                            'confidence': conf,
                                            'bbox': {
                                                'x1': int(x1), 'y1': int(y1),
                                                'x2': int(x2), 'y2': int(y2)
                                            },
                                            'area': (x2 - x1) * (y2 - y1),
                                            'detection_strategy': f'multi_scale_{scale}',
                                            'model_name': model_name
                                        }
                                        detections.append(detection)
                except Exception as e:
                    logger.debug(f"Multi-scale detection failed for {scale}: {e}")
            
            # Process standard results
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        if class_id < len(self.class_names):
                            class_name = self.class_names[class_id]
                            
                            # Check if it's a vehicle
                            vehicle_type = self._classify_vehicle(class_name)
                            if vehicle_type:
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                
                                detection = {
                                    'class': vehicle_type,
                                    'original_class': class_name,
                                    'confidence': conf,
                                    'bbox': {
                                        'x1': int(x1), 'y1': int(y1),
                                        'x2': int(x2), 'y2': int(y2)
                                    },
                                    'area': (x2 - x1) * (y2 - y1),
                                    'detection_strategy': 'standard',
                                    'model_name': model_name
                                }
                                detections.append(detection)
            
        except Exception as e:
            logger.error(f"Detection failed for {model_name}: {e}")
        
        return detections
    
    def _classify_vehicle(self, class_name: str) -> Optional[str]:
        """Classify detected object as vehicle type"""
        class_name = class_name.lower()
        
        # Use the vehicle class mapping to convert COCO classes to our 3-category system
        if class_name in self.vehicle_class_mapping:
            return self.vehicle_class_mapping[class_name]
        
        return None
    
    def _advanced_post_processing(self, ensemble_results: Dict, image_size: Tuple[int, int]) -> Dict[str, Any]:
        """Advanced post-processing with NMS, clustering, and ensemble fusion"""
        
        all_detections = ensemble_results['all_detections']
        
        if not all_detections:
            return self._empty_results()
        
        logger.info(f"Post-processing {len(all_detections)} raw detections")
        
        # Step 1: Weighted Non-Maximum Suppression
        nms_detections = self._weighted_nms(all_detections, iou_threshold=0.5)
        
        # Step 2: Ensemble fusion (combine overlapping detections from different models)
        fused_detections = self._ensemble_fusion(nms_detections, iou_threshold=0.3)
        
        # Step 3: Confidence calibration
        calibrated_detections = self._calibrate_confidence(fused_detections)
        
        # Step 4: Size and position filtering
        filtered_detections = self._filter_detections(calibrated_detections, image_size)
        
        # Generate final results
        return self._generate_final_results(filtered_detections, ensemble_results)
    
    def _weighted_nms(self, detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """Weighted Non-Maximum Suppression considering model weights"""
        
        if not detections:
            return []
        
        # Sort by weighted confidence (confidence * model_weight)
        detections.sort(key=lambda x: x['confidence'] * x.get('model_weight', 1), reverse=True)
        
        keep = []
        used = set()
        
        for i, detection in enumerate(detections):
            if i in used:
                continue
            
            keep.append(detection)
            
            # Find overlapping detections
            for j, other_detection in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                
                iou = self._calculate_iou(detection['bbox'], other_detection['bbox'])
                if iou > iou_threshold and detection['class'] == other_detection['class']:
                    used.add(j)
        
        logger.info(f"NMS: {len(detections)} -> {len(keep)} detections")
        return keep
    
    def _ensemble_fusion(self, detections: List[Dict], iou_threshold: float = 0.3) -> List[Dict]:
        """Fuse detections from different models"""
        
        if not detections:
            return []
        
        fused = []
        used = set()
        
        for i, detection in enumerate(detections):
            if i in used:
                continue
            
            # Find similar detections from other models
            similar_detections = [detection]
            similar_indices = {i}
            
            for j, other_detection in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                
                iou = self._calculate_iou(detection['bbox'], other_detection['bbox'])
                if (iou > iou_threshold and 
                    detection['class'] == other_detection['class'] and
                    detection.get('source_model') != other_detection.get('source_model')):
                    
                    similar_detections.append(other_detection)
                    similar_indices.add(j)
            
            # Fuse similar detections
            if len(similar_detections) > 1:
                fused_detection = self._fuse_detections(similar_detections)
                fused.append(fused_detection)
            else:
                fused.append(detection)
            
            used.update(similar_indices)
        
        logger.info(f"Ensemble fusion: {len(detections)} -> {len(fused)} detections")
        return fused
    
    def _fuse_detections(self, detections: List[Dict]) -> Dict:
        """Fuse multiple detections into one with weighted averaging"""
        
        total_weight = sum(d.get('model_weight', 1) for d in detections)
        
        # Weighted average of bounding boxes
        weighted_bbox = {
            'x1': sum(d['bbox']['x1'] * d.get('model_weight', 1) for d in detections) / total_weight,
            'y1': sum(d['bbox']['y1'] * d.get('model_weight', 1) for d in detections) / total_weight,
            'x2': sum(d['bbox']['x2'] * d.get('model_weight', 1) for d in detections) / total_weight,
            'y2': sum(d['bbox']['y2'] * d.get('model_weight', 1) for d in detections) / total_weight
        }
        
        # Convert to integers
        weighted_bbox = {k: int(v) for k, v in weighted_bbox.items()}
        
        # Weighted confidence
        weighted_confidence = sum(d['confidence'] * d.get('model_weight', 1) for d in detections) / total_weight
        
        # Use the most confident detection's class
        best_detection = max(detections, key=lambda x: x['confidence'])
        
        return {
            'class': best_detection['class'],
            'original_class': best_detection['original_class'],
            'confidence': weighted_confidence,
            'bbox': weighted_bbox,
            'area': (weighted_bbox['x2'] - weighted_bbox['x1']) * (weighted_bbox['y2'] - weighted_bbox['y1']),
            'detection_strategy': 'ensemble_fusion',
            'model_consensus': len(detections),
            'source_models': list(set(d.get('source_model', 'unknown') for d in detections)),
            'ensemble_weight': total_weight
        }
    
    def _calibrate_confidence(self, detections: List[Dict]) -> List[Dict]:
        """Calibrate confidence scores based on ensemble agreement"""
        
        for detection in detections:
            original_confidence = detection['confidence']
            consensus_count = detection.get('model_consensus', 1)
            
            # Boost confidence for detections agreed upon by multiple models
            if consensus_count > 1:
                consensus_boost = min(0.2, (consensus_count - 1) * 0.1)
                detection['confidence'] = min(1.0, original_confidence + consensus_boost)
                detection['confidence_calibrated'] = True
            else:
                detection['confidence_calibrated'] = False
        
        return detections
    
    def _filter_detections(self, detections: List[Dict], image_size: Tuple[int, int]) -> List[Dict]:
        """Filter detections based on size, position, and quality"""
        
        width, height = image_size
        filtered = []
        
        for detection in detections:
            bbox = detection['bbox']
            area = detection['area']
            confidence = detection['confidence']
            
            # Size filtering
            if area < 100:  # Too small
                continue
            if area > width * height * 0.8:  # Too large (likely false positive)
                continue
            
            # Position filtering (remove detections at image edges that might be cut off)
            if (bbox['x1'] <= 5 or bbox['y1'] <= 5 or 
                bbox['x2'] >= width - 5 or bbox['y2'] >= height - 5):
                if area < 5000:  # Only filter small edge detections
                    continue
            
            # Aspect ratio filtering
            bbox_width = bbox['x2'] - bbox['x1']
            bbox_height = bbox['y2'] - bbox['y1']
            aspect_ratio = bbox_width / max(bbox_height, 1)
            
            if aspect_ratio > 5 or aspect_ratio < 0.2:  # Unrealistic aspect ratios
                continue
            
            # Confidence filtering (dynamic based on detection quality) - ultra-low for dense traffic
            min_confidence = 0.01 if detection.get('model_consensus', 1) > 1 else 0.02  # Much lower thresholds
            if confidence < min_confidence:
                continue
            
            filtered.append(detection)
        
        logger.info(f"Filtering: {len(detections)} -> {len(filtered)} detections")
        return filtered
    
    def _generate_final_results(self, detections: List[Dict], ensemble_results: Dict) -> Dict[str, Any]:
        """Generate final comprehensive results"""
        
        # Count vehicles by type
        vehicle_counts = {'car': 0, 'large_vehicle': 0, '2-wheeler': 0}
        total_vehicles = len(detections)
        total_confidence = sum(d['confidence'] for d in detections)
        avg_confidence = total_confidence / total_vehicles if total_vehicles > 0 else 0
        
        for detection in detections:
            vehicle_type = detection['class']
            if vehicle_type in vehicle_counts:
                vehicle_counts[vehicle_type] += 1
        
        # Generate detailed breakdown
        vehicle_breakdown = self._generate_advanced_breakdown(detections)
        
        # Ensemble information
        ensemble_info = {
            'models_used': list(self.models.keys()),
            'total_raw_detections': ensemble_results['total_raw_detections'],
            'final_detections': total_vehicles,
            'detection_efficiency': total_vehicles / max(ensemble_results['total_raw_detections'], 1),
            'consensus_detections': len([d for d in detections if d.get('model_consensus', 1) > 1]),
            'single_model_detections': len([d for d in detections if d.get('model_consensus', 1) == 1])
        }
        
        return {
            'final_detections': detections,
            'vehicle_counts': vehicle_counts,
            'total_vehicles': total_vehicles,
            'average_confidence': avg_confidence,
            'detection_summary': {
                'cars': vehicle_counts['car'],
                'large_vehicles': vehicle_counts['large_vehicle'],
                '2_wheelers': vehicle_counts['2-wheeler']
            },
            'vehicle_breakdown': vehicle_breakdown,
            'ensemble_info': ensemble_info
        }
    
    def _generate_advanced_breakdown(self, detections: List[Dict]) -> Dict[str, Any]:
        """Generate advanced vehicle breakdown with ensemble information"""
        
        breakdown = {
            'by_type': {},
            'by_confidence': {'very_high': 0, 'high': 0, 'medium': 0, 'low': 0},
            'by_consensus': {'multi_model': 0, 'single_model': 0},
            'by_size': {'small': 0, 'medium': 0, 'large': 0, 'very_large': 0},
            'detailed_list': []
        }
        
        for i, detection in enumerate(detections):
            vehicle_class = detection['class']
            confidence = detection['confidence']
            area = detection['area']
            consensus = detection.get('model_consensus', 1)
            
            # Count by type
            if vehicle_class not in breakdown['by_type']:
                breakdown['by_type'][vehicle_class] = {
                    'count': 0,
                    'avg_confidence': 0,
                    'confidence_range': {'min': 1.0, 'max': 0.0},
                    'consensus_detections': 0,
                    'source_models': set()
                }
            
            type_info = breakdown['by_type'][vehicle_class]
            type_info['count'] += 1
            type_info['confidence_range']['min'] = min(type_info['confidence_range']['min'], confidence)
            type_info['confidence_range']['max'] = max(type_info['confidence_range']['max'], confidence)
            
            if consensus > 1:
                type_info['consensus_detections'] += 1
            
            source_models = detection.get('source_models', [detection.get('source_model', 'unknown')])
            type_info['source_models'].update(source_models)
            
            # Count by confidence level
            if confidence >= 0.8:
                breakdown['by_confidence']['very_high'] += 1
            elif confidence >= 0.6:
                breakdown['by_confidence']['high'] += 1
            elif confidence >= 0.4:
                breakdown['by_confidence']['medium'] += 1
            else:
                breakdown['by_confidence']['low'] += 1
            
            # Count by consensus
            if consensus > 1:
                breakdown['by_consensus']['multi_model'] += 1
            else:
                breakdown['by_consensus']['single_model'] += 1
            
            # Count by size
            if area < 5000:
                size_cat = 'small'
            elif area < 15000:
                size_cat = 'medium'
            elif area < 30000:
                size_cat = 'large'
            else:
                size_cat = 'very_large'
            
            breakdown['by_size'][size_cat] += 1
            
            # Add to detailed list
            breakdown['detailed_list'].append({
                'id': i + 1,
                'type': vehicle_class,
                'original_class': detection.get('original_class', vehicle_class),
                'confidence': f"{confidence:.1%}",
                'confidence_raw': confidence,
                'size': size_cat,
                'area': int(area),
                'consensus': consensus,
                'source_models': source_models,
                'detection_strategy': detection.get('detection_strategy', 'standard'),
                'calibrated': detection.get('confidence_calibrated', False),
                'quality': 'excellent' if confidence >= 0.8 else 'very_good' if confidence >= 0.6 else 'good' if confidence >= 0.4 else 'fair'
            })
        
        # Calculate average confidences
        for vehicle_class, info in breakdown['by_type'].items():
            class_detections = [d for d in detections if d['class'] == vehicle_class]
            if class_detections:
                info['avg_confidence'] = sum(d['confidence'] for d in class_detections) / len(class_detections)
                info['source_models'] = list(info['source_models'])
        
        return breakdown
    
    def _analyze_traffic_density_advanced(self, results: Dict, image_size: Tuple[int, int]) -> Dict[str, Any]:
        """Advanced traffic density analysis"""
        
        width, height = image_size
        total_vehicles = results['total_vehicles']
        detections = results['final_detections']
        
        if total_vehicles == 0:
            return {
                'density_level': 'Empty',
                'congestion_index': 0.0,
                'flow_state': 'No Traffic',
                'vehicles_per_area': 0.0,
                'coverage_percentage': 0.0
            }
        
        # Calculate advanced metrics
        image_area = width * height
        total_vehicle_area = sum(d['area'] for d in detections)
        coverage_percentage = (total_vehicle_area / image_area) * 100
        vehicles_per_1000px = (total_vehicles / image_area) * 1000
        
        # Advanced density classification with realistic thresholds
        if total_vehicles <= 2:
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
        
        # Adjust based on coverage
        if coverage_percentage > 25:
            congestion_index = min(1.0, congestion_index + 0.1)
            if density_level in ['Light', 'Moderate']:
                density_level = 'Heavy'
        
        # Flow state estimation
        if congestion_index >= 0.9:
            flow_state = 'Stop and Go'
        elif congestion_index >= 0.7:
            flow_state = 'Slow Moving'
        elif congestion_index >= 0.4:
            flow_state = 'Moderate Flow'
        elif congestion_index >= 0.2:
            flow_state = 'Good Flow'
        else:
            flow_state = 'Free Flow'
        
        return {
            'density_level': density_level,
            'congestion_index': congestion_index,
            'flow_state': flow_state,
            'vehicles_per_area': vehicles_per_1000px,
            'coverage_percentage': coverage_percentage,
            'total_vehicles': total_vehicles,
            'advanced_metrics': {
                'vehicle_density_score': min(100, total_vehicles * 2),
                'spatial_distribution': self._analyze_spatial_distribution(detections, image_size),
                'size_diversity': self._analyze_size_diversity(detections),
                'confidence_quality': results['average_confidence']
            }
        }
    
    def _analyze_spatial_distribution(self, detections: List[Dict], image_size: Tuple[int, int]) -> str:
        """Analyze how vehicles are distributed spatially"""
        if not detections:
            return 'none'
        
        width, height = image_size
        
        # Divide image into quadrants
        centers = []
        for detection in detections:
            bbox = detection['bbox']
            center_x = (bbox['x1'] + bbox['x2']) / 2 / width
            center_y = (bbox['y1'] + bbox['y2']) / 2 / height
            centers.append((center_x, center_y))
        
        # Count vehicles in each quadrant
        quadrants = {'tl': 0, 'tr': 0, 'bl': 0, 'br': 0}
        for x, y in centers:
            if x < 0.5 and y < 0.5:
                quadrants['tl'] += 1
            elif x >= 0.5 and y < 0.5:
                quadrants['tr'] += 1
            elif x < 0.5 and y >= 0.5:
                quadrants['bl'] += 1
            else:
                quadrants['br'] += 1
        
        # Determine distribution pattern
        max_count = max(quadrants.values())
        min_count = min(quadrants.values())
        
        if max_count - min_count <= 1:
            return 'uniform'
        elif max_count > len(detections) * 0.6:
            return 'concentrated'
        else:
            return 'scattered'
    
    def _analyze_size_diversity(self, detections: List[Dict]) -> str:
        """Analyze diversity of vehicle sizes"""
        if not detections:
            return 'none'
        
        areas = [d['area'] for d in detections]
        area_std = np.std(areas)
        area_mean = np.mean(areas)
        
        coefficient_of_variation = area_std / area_mean if area_mean > 0 else 0
        
        if coefficient_of_variation > 0.8:
            return 'high_diversity'
        elif coefficient_of_variation > 0.4:
            return 'moderate_diversity'
        else:
            return 'low_diversity'
    
    def _calculate_iou(self, bbox1: Dict, bbox2: Dict) -> float:
        """Calculate Intersection over Union"""
        try:
            x1 = max(bbox1['x1'], bbox2['x1'])
            y1 = max(bbox1['y1'], bbox2['y1'])
            x2 = min(bbox1['x2'], bbox2['x2'])
            y2 = min(bbox1['y2'], bbox2['y2'])
            
            if x2 <= x1 or y2 <= y1:
                return 0.0
            
            intersection = (x2 - x1) * (y2 - y1)
            
            area1 = (bbox1['x2'] - bbox1['x1']) * (bbox1['y2'] - bbox1['y1'])
            area2 = (bbox2['x2'] - bbox2['x1']) * (bbox2['y2'] - bbox2['y1'])
            union = area1 + area2 - intersection
            
            return intersection / union if union > 0 else 0.0
        except:
            return 0.0
    
    def _empty_results(self) -> Dict[str, Any]:
        """Return empty results structure"""
        return {
            'final_detections': [],
            'vehicle_counts': {'car': 0, 'large_vehicle': 0, '2-wheeler': 0},
            'total_vehicles': 0,
            'average_confidence': 0.0,
            'detection_summary': {'cars': 0, 'large_vehicles': 0, '2_wheelers': 0},
            'vehicle_breakdown': {
                'by_type': {},
                'by_confidence': {'very_high': 0, 'high': 0, 'medium': 0, 'low': 0},
                'by_consensus': {'multi_model': 0, 'single_model': 0},
                'detailed_list': []
            },
            'ensemble_info': {
                'models_used': list(self.models.keys()),
                'total_raw_detections': 0,
                'final_detections': 0,
                'detection_efficiency': 0.0
            }
        }
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