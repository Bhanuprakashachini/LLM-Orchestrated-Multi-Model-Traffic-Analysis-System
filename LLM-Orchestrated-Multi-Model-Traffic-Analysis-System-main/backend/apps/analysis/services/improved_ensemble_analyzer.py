"""
Improved Ensemble Analyzer - Combines YOLOv8, YOLOv11, YOLOv12 with intelligent fusion
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
import logging
from collections import defaultdict

from .improved_yolov8_analyzer import ImprovedYOLOv8Analyzer
from .improved_yolov11_analyzer import ImprovedYOLOv11Analyzer
from .improved_yolov12_analyzer import ImprovedYOLOv12Analyzer

logger = logging.getLogger(__name__)

class ImprovedEnsembleAnalyzer:
    """
    Intelligent ensemble that combines multiple YOLO models for best accuracy
    """
    
    def __init__(self, confidence_threshold: float = 0.25):
        self.base_confidence_threshold = confidence_threshold  # Store base threshold
        self.confidence_threshold = confidence_threshold
        
        # Initialize all models
        self.models = {}
        self.model_weights = {}  # Performance-based weights
        
        try:
            self.models['yolov8'] = ImprovedYOLOv8Analyzer(confidence_threshold=confidence_threshold)
            self.model_weights['yolov8'] = 1.0
            logger.info("YOLOv8 model loaded for ensemble")
        except Exception as e:
            logger.warning(f"YOLOv8 not available for ensemble: {e}")
        
        try:
            self.models['yolov11'] = ImprovedYOLOv11Analyzer(confidence_threshold=confidence_threshold)
            self.model_weights['yolov11'] = 1.1  # Slightly higher weight (newer model)
            logger.info("YOLOv11 model loaded for ensemble")
        except Exception as e:
            logger.warning(f"YOLOv11 not available for ensemble: {e}")
        
        try:
            self.models['yolov12'] = ImprovedYOLOv12Analyzer(confidence_threshold=confidence_threshold)
            self.model_weights['yolov12'] = 1.2  # Highest weight (newest model)
            logger.info("YOLOv12 model loaded for ensemble")
        except Exception as e:
            logger.warning(f"YOLOv12 not available for ensemble: {e}")
        
        if not self.models:
            raise RuntimeError("No YOLO models available for ensemble")
        
        logger.info(f"Ensemble initialized with {len(self.models)} models: {list(self.models.keys())}")
    
    def detect_vehicles_ensemble(self, image: np.ndarray) -> List[Dict]:
        """
        Run ensemble detection with intelligent fusion
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of fused detection dictionaries
        """
        all_detections = {}
        model_results = {}
        
        # Run all models
        for model_name, model in self.models.items():
            try:
                start_time = time.time()
                detections = model.detect_vehicles(image)
                processing_time = time.time() - start_time
                
                all_detections[model_name] = detections
                model_results[model_name] = {
                    'detections': len(detections),
                    'processing_time': processing_time,
                    'avg_confidence': np.mean([d['confidence'] for d in detections]) if detections else 0.0
                }
                
                logger.info(f"{model_name}: {len(detections)} detections, {processing_time:.3f}s")
                
            except Exception as e:
                logger.error(f"Model {model_name} failed: {e}")
                all_detections[model_name] = []
                model_results[model_name] = {'detections': 0, 'processing_time': 0, 'avg_confidence': 0.0}
        
        # Fuse detections intelligently
        fused_detections = self._fuse_detections(all_detections, image.shape)
        
        logger.info(f"Ensemble fusion: {len(fused_detections)} final detections")
        return fused_detections
    
    def _fuse_detections(self, all_detections: Dict[str, List[Dict]], 
                        image_shape: Tuple[int, int, int]) -> List[Dict]:
        """
        Intelligently fuse detections from multiple models
        
        Args:
            all_detections: Dictionary of model_name -> detections
            image_shape: Shape of input image
            
        Returns:
            List of fused detections
        """
        if not all_detections:
            return []
        
        # Collect all detections with model info
        all_dets = []
        for model_name, detections in all_detections.items():
            for det in detections:
                det_copy = det.copy()
                det_copy['source_model'] = model_name
                det_copy['weighted_confidence'] = det['confidence'] * self.model_weights.get(model_name, 1.0)
                all_dets.append(det_copy)
        
        if not all_dets:
            return []
        
        # Group similar detections
        detection_groups = self._group_similar_detections(all_dets)
        
        # Fuse each group
        fused_detections = []
        for group in detection_groups:
            fused_det = self._fuse_detection_group(group)
            if fused_det:
                fused_detections.append(fused_det)
        
        # Final filtering and sorting
        fused_detections = self._final_filtering(fused_detections, image_shape)
        
        return fused_detections
    
    def _group_similar_detections(self, detections: List[Dict], iou_threshold: float = 0.3) -> List[List[Dict]]:
        """
        Group detections that likely represent the same vehicle
        
        Args:
            detections: List of all detections
            iou_threshold: IoU threshold for grouping
            
        Returns:
            List of detection groups
        """
        groups = []
        used = set()
        
        for i, det1 in enumerate(detections):
            if i in used:
                continue
            
            group = [det1]
            used.add(i)
            
            for j, det2 in enumerate(detections[i+1:], i+1):
                if j in used:
                    continue
                
                iou = self._calculate_iou(det1['bbox'], det2['bbox'])
                if iou > iou_threshold:
                    group.append(det2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _validate_motorcycle_detection(self, detection: Dict, image_shape: Tuple[int, int, int]) -> bool:
        """
        Validate motorcycle detection to reduce false positives while keeping real motorcycles
        
        Args:
            detection: Detection dictionary with bbox, confidence, etc.
            image_shape: Shape of input image
            
        Returns:
            True if detection is likely a real motorcycle
        """
        bbox = detection['bbox']
        confidence = detection['confidence']
        x1, y1, x2, y2 = bbox
        
        height, width = image_shape[:2]
        
        # Calculate properties
        det_width = x2 - x1
        det_height = y2 - y1
        det_area = det_width * det_height
        aspect_ratio = det_width / det_height if det_height > 0 else 0
        centroid_x = (x1 + x2) / 2
        centroid_y = (y1 + y2) / 2
        rel_y = centroid_y / height
        
        # Motorcycle validation criteria (more lenient for real motorcycles)
        
        # 1. Size validation - motorcycles can be small but not too tiny or huge
        if det_area < 500:  # Too small (less than ~22x22 pixels)
            return False
        if det_area > 15000:  # Too large for a motorcycle
            return False
        
        # 2. Aspect ratio - motorcycles have reasonable proportions
        if aspect_ratio < 0.2 or aspect_ratio > 4.0:  # Very extreme ratios
            return False
        
        # 3. Position validation - motorcycles should be on road area
        if rel_y < 0.1:  # Too high (sky area)
            return False
        if rel_y > 0.99:  # Too low (bottom edge artifacts)
            return False
        
        # 4. Context-based validation for dense traffic
        # In dense traffic, motorcycles often have lower confidence but are real
        # So we're more lenient with confidence for reasonable-sized detections
        
        # 5. Multi-model agreement bonus (ensemble specific)
        model_agreement = detection.get('model_agreement', 1)
        if model_agreement > 1:  # Multiple models agree
            # More lenient validation for multi-model detections
            return True
        
        # 6. For single-model detections, be slightly more strict
        if confidence < 0.001:  # Extremely low confidence
            # Additional size check for very low confidence
            if det_area < 1000:  # Small and very low confidence
                return False
        
        return True
    
    def _fuse_detection_group(self, group: List[Dict]) -> Optional[Dict]:
        """
        Fuse a group of similar detections into one
        
        Args:
            group: List of similar detections
            
        Returns:
            Fused detection or None
        """
        if not group:
            return None
        
        if len(group) == 1:
            # Add required fields for single detections
            single_det = group[0].copy()
            single_det['model_agreement'] = 1
            single_det['total_models'] = len(self.models)
            single_det['source_models'] = [single_det['source_model']]
            single_det['individual_confidences'] = [single_det['confidence']]
            return single_det
        
        # Calculate weighted average of bounding boxes
        total_weight = sum(det['weighted_confidence'] for det in group)
        
        if total_weight == 0:
            return None
        
        # Weighted average of bbox coordinates
        avg_bbox = [0, 0, 0, 0]
        for det in group:
            weight = det['weighted_confidence'] / total_weight
            for i in range(4):
                avg_bbox[i] += det['bbox'][i] * weight
        
        # Determine class by majority vote (weighted)
        class_votes = defaultdict(float)
        for det in group:
            class_votes[det['class_name']] += det['weighted_confidence']
        
        best_class = max(class_votes.keys(), key=lambda k: class_votes[k])
        
        # Calculate ensemble confidence
        ensemble_confidence = min(1.0, total_weight / len(group))
        
        # Count model agreement
        model_agreement = len(set(det['source_model'] for det in group))
        
        fused_detection = {
            'bbox': avg_bbox,
            'confidence': ensemble_confidence,
            'class_name': best_class,
            'centroid': [(avg_bbox[0] + avg_bbox[2]) / 2, (avg_bbox[1] + avg_bbox[3]) / 2],
            'model_agreement': model_agreement,
            'total_models': len(self.models),
            'source_models': [det['source_model'] for det in group],
            'individual_confidences': [det['confidence'] for det in group]
        }
        
        return fused_detection
    
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
    
    def _final_filtering(self, detections: List[Dict], 
                        image_shape: Tuple[int, int, int]) -> List[Dict]:
        """
        Apply final filtering to ensemble results
        
        Args:
            detections: List of fused detections
            image_shape: Shape of input image
            
        Returns:
            Filtered detections
        """
        if not detections:
            return []
        
        # Filter by ensemble confidence and model agreement
        filtered = []
        for det in detections:
            # Require minimum confidence
            if det['confidence'] < self.confidence_threshold:
                continue
            
            # Apply motorcycle-specific validation
            if det['class_name'] == 'motorcycle':
                if not self._validate_motorcycle_detection(det, image_shape):
                    continue  # Skip invalid motorcycle detections
            
            # Prefer detections agreed upon by multiple models
            # Handle single detections that don't have model_agreement
            model_agreement = det.get('model_agreement', 1)  # Default to 1 for single detections
            total_models = det.get('total_models', len(self.models))
            
            agreement_bonus = model_agreement / total_models
            adjusted_confidence = det['confidence'] * (1 + agreement_bonus)
            
            if adjusted_confidence >= self.confidence_threshold:
                det['adjusted_confidence'] = adjusted_confidence
                filtered.append(det)
        
        # Sort by adjusted confidence (highest first)
        filtered.sort(key=lambda x: x['adjusted_confidence'], reverse=True)
        
        return filtered
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze single image with ensemble and return comprehensive results
        
        Args:
            image_path: Path to image file
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            start_time = time.time()
            
            # Run ensemble detection
            detections = self.detect_vehicles_ensemble(image)
            
            processing_time = time.time() - start_time
            
            # Get image conditions from the first available model
            image_conditions = {}
            for model_name, model in self.models.items():
                try:
                    # Use the individual model's condition analysis
                    if hasattr(model, '_analyze_image_conditions'):
                        image_conditions = model._analyze_image_conditions(image)
                        break
                except Exception as e:
                    logger.warning(f"Failed to get conditions from {model_name}: {e}")
                    continue
            
            # Count vehicles by type and group them properly
            raw_vehicle_counts = {}
            for detection in detections:
                class_name = detection['class_name']
                raw_vehicle_counts[class_name] = raw_vehicle_counts.get(class_name, 0) + 1
            
            # Create the expected vehicle_breakdown structure for comprehensive service compatibility
            vehicle_breakdown = {
                'by_type': {
                    'car': {
                        'count': raw_vehicle_counts.get('car', 0),
                        'avg_confidence': np.mean([d['confidence'] for d in detections if d['class_name'] == 'car']) if any(d['class_name'] == 'car' for d in detections) else 0.0
                    },
                    'truck': {
                        'count': raw_vehicle_counts.get('truck', 0),
                        'avg_confidence': np.mean([d['confidence'] for d in detections if d['class_name'] == 'truck']) if any(d['class_name'] == 'truck' for d in detections) else 0.0
                    },
                    'bus': {
                        'count': raw_vehicle_counts.get('bus', 0),
                        'avg_confidence': np.mean([d['confidence'] for d in detections if d['class_name'] == 'bus']) if any(d['class_name'] == 'bus' for d in detections) else 0.0
                    },
                    'motorcycle': {
                        'count': raw_vehicle_counts.get('motorcycle', 0),
                        'avg_confidence': np.mean([d['confidence'] for d in detections if d['class_name'] == 'motorcycle']) if any(d['class_name'] == 'motorcycle' for d in detections) else 0.0
                    },
                    'bicycle': {
                        'count': raw_vehicle_counts.get('bicycle', 0),
                        'avg_confidence': np.mean([d['confidence'] for d in detections if d['class_name'] == 'bicycle']) if any(d['class_name'] == 'bicycle' for d in detections) else 0.0
                    }
                }
            }
            
            # Group vehicle counts into the expected categories
            grouped_vehicle_counts = {
                'cars': raw_vehicle_counts.get('car', 0),
                'large_vehicles': raw_vehicle_counts.get('truck', 0) + raw_vehicle_counts.get('bus', 0),
                '2_wheelers': raw_vehicle_counts.get('motorcycle', 0) + raw_vehicle_counts.get('bicycle', 0)
            }
            
            logger.info(f"🚗 Ensemble vehicle breakdown: Raw={raw_vehicle_counts}, Grouped={grouped_vehicle_counts}")
            logger.info(f"📊 Vehicle breakdown structure: {vehicle_breakdown}")
            
            # Calculate metrics
            total_vehicles = len(detections)
            avg_confidence = np.mean([d['confidence'] for d in detections]) if detections else 0.0
            avg_agreement = np.mean([d['model_agreement'] for d in detections]) if detections else 0.0
            
            results = {
                'model_name': 'Ensemble_Improved',
                'image_path': image_path,
                'total_vehicles': total_vehicles,
                'vehicle_counts': grouped_vehicle_counts,  # Use grouped counts (for backward compatibility)
                'vehicle_breakdown': vehicle_breakdown,  # Add proper structure for comprehensive service
                'raw_vehicle_counts': raw_vehicle_counts,  # Keep raw counts for debugging
                'detections': detections,
                'processing_time': processing_time,
                'average_confidence': float(avg_confidence),
                'average_model_agreement': float(avg_agreement),
                'available_models': list(self.models.keys()),
                'image_shape': image.shape,
                'image_conditions': image_conditions,  # Add image conditions
                'success': True
            }
            
            logger.info(f"✅ Ensemble analysis complete: {total_vehicles} vehicles detected")
            logger.info(f"📊 Returning vehicle_breakdown: {vehicle_breakdown}")
            return results
            
        except Exception as e:
            logger.error(f"Ensemble analysis failed: {e}")
            return {
                'model_name': 'Ensemble_Improved',
                'image_path': image_path,
                'success': False,
                'error': str(e)
            }
    
    def create_annotated_image(self, image_path: str, output_path: str) -> bool:
        """
        Create annotated image with ensemble detection results
        
        Args:
            image_path: Input image path
            output_path: Output annotated image path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            # Get detections
            detections = self.detect_vehicles_ensemble(image)
            
            # Draw annotations
            annotated_image = image.copy()
            
            for detection in detections:
                x1, y1, x2, y2 = [int(coord) for coord in detection['bbox']]
                confidence = detection['confidence']
                class_name = detection['class_name']
                agreement = detection['model_agreement']
                
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
                
                # Thicker box for higher agreement
                thickness = 2 + agreement
                
                # Draw bounding box
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, thickness)
                
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
                
                # Draw label with grouped category and agreement info
                label = f"Ens-{display_class}: {confidence:.2f} ({agreement}/{len(self.models)})"
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
            summary = f"Ensemble ({len(self.models)} models): {total_vehicles} vehicles detected"
            cv2.putText(annotated_image, summary,
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                       (0, 255, 255), 2)
            
            # Save annotated image
            success = cv2.imwrite(output_path, annotated_image)
            
            if success:
                logger.info(f"Ensemble annotated image saved: {output_path}")
            else:
                logger.error(f"Failed to save ensemble annotated image: {output_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ensemble annotation failed: {e}")
            return False