"""
Enhanced Video Analysis Service with Vehicle Tracking and Comprehensive Metrics
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, deque
import time
import os
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class VehicleTracker:
    """Advanced vehicle tracking across video frames"""
    
    def __init__(self, max_disappeared=10, max_distance=100):
        self.next_id = 0
        self.objects = {}  # {id: centroid}
        self.disappeared = {}  # {id: frames_disappeared}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        
    def register(self, centroid):
        """Register a new object"""
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.next_id += 1
        return self.next_id - 1
        
    def deregister(self, object_id):
        """Deregister an object"""
        del self.objects[object_id]
        del self.disappeared[object_id]
        
    def update(self, detections):
        """Update tracker with new detections"""
        if len(detections) == 0:
            # Mark all existing objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return {}
            
        input_centroids = np.array([det['centroid'] for det in detections])
        
        if len(self.objects) == 0:
            # Register all detections as new objects
            tracking_results = {}
            for i, detection in enumerate(detections):
                track_id = self.register(input_centroids[i])
                tracking_results[track_id] = detection
            return tracking_results
            
        # Compute distance matrix
        object_centroids = np.array(list(self.objects.values()))
        D = np.linalg.norm(object_centroids[:, np.newaxis] - input_centroids, axis=2)
        
        # Find minimum values and sort by distance
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]
        
        used_row_indices = set()
        used_col_indices = set()
        tracking_results = {}
        
        object_ids = list(self.objects.keys())
        
        for (row, col) in zip(rows, cols):
            if row in used_row_indices or col in used_col_indices:
                continue
                
            if D[row, col] > self.max_distance:
                continue
                
            object_id = object_ids[row]
            self.objects[object_id] = input_centroids[col]
            self.disappeared[object_id] = 0
            tracking_results[object_id] = detections[col]
            
            used_row_indices.add(row)
            used_col_indices.add(col)
            
        # Handle unmatched detections and objects
        unused_row_indices = set(range(0, D.shape[0])).difference(used_row_indices)
        unused_col_indices = set(range(0, D.shape[1])).difference(used_col_indices)
        
        if D.shape[0] >= D.shape[1]:
            # More existing objects than detections
            for row in unused_row_indices:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
        else:
            # More detections than existing objects
            for col in unused_col_indices:
                track_id = self.register(input_centroids[col])
                tracking_results[track_id] = detections[col]
                
        return tracking_results

class EnhancedVideoAnalyzer:
    """Enhanced video analyzer with tracking and comprehensive metrics"""
    
    def __init__(self, model_path=None, confidence_threshold=0.05, roi_polygon=None, enable_roi_filtering=True):
        """
        Initialize Enhanced Video Analyzer with ROI filtering
        """
        if model_path is None:
            model_path = os.path.join('backend', 'mod
        
        Args:
            model_path: Path to YOLO model
            confidence_threshold: Detection confidence threshold (lowered for better detection)
            roi_polygon: List of (x, y) points defining the region of interest (road area)
                        If None, uses automatic road detection
            enable_roi_filtering: Whether to apply ROI filtering (disable for dense traffic)
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.roi_polygon = roi_polygon
        self.enable_roi_filtering = enable_roi_filtering
        self.vehicle_classes = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
        self.tracker = VehicleTracker()
        
        # Vehicle class mapping for YOLO
        self.class_mapping = {
            2: 'car',           # car
            3: 'motorcycle',    # motorcycle  
            5: 'bus',          # bus
            7: 'truck',        # truck
            1: 'bicycle'       # bicycle
        }
        
        logger.info(f"Enhanced Video Analyzer initialized with model: {model_path}")
        logger.info(f"Confidence threshold: {confidence_threshold}")
        if roi_polygon:
            logger.info(f"ROI polygon defined with {len(roi_polygon)} points")
    
    def _detect_road_area(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Automatically detect road area using image processing
        Returns a binary mask where road area is white (255)
        """
        try:
            # Convert to HSV for better road detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Define road color ranges (gray/dark colors)
            # Adjust these ranges based on your specific road conditions
            lower_road1 = np.array([0, 0, 0])      # Dark colors
            upper_road1 = np.array([180, 50, 100])
            
            lower_road2 = np.array([0, 0, 50])     # Gray colors  
            upper_road2 = np.array([180, 30, 150])
            
            # Create masks for road colors
            mask1 = cv2.inRange(hsv, lower_road1, upper_road1)
            mask2 = cv2.inRange(hsv, lower_road2, upper_road2)
            road_mask = cv2.bitwise_or(mask1, mask2)
            
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_CLOSE, kernel)
            road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_OPEN, kernel)
            
            # Find the largest contour (likely the main road)
            contours, _ = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Create a clean mask from the largest contour
                clean_mask = np.zeros_like(road_mask)
                cv2.fillPoly(clean_mask, [largest_contour], 255)
                
                return clean_mask
            
            return None
            
        except Exception as e:
            logger.warning(f"Road detection failed: {e}")
            return None
    
    def _is_in_roi(self, centroid: List[float], frame_shape: Tuple[int, int]) -> bool:
        """
        Check if a detection centroid is within the region of interest
        
        Args:
            centroid: [x, y] coordinates of detection center
            frame_shape: (height, width) of the frame
            
        Returns:
            True if centroid is within ROI, False otherwise
        """
        if self.roi_polygon:
            # Use predefined ROI polygon
            point = (int(centroid[0]), int(centroid[1]))
            return cv2.pointPolygonTest(np.array(self.roi_polygon, dtype=np.int32), point, False) >= 0
        
        # If no ROI defined, use lenient height-based filtering for dense traffic
        # Only exclude the very top portion which is likely sky/buildings
        height_threshold = frame_shape[0] * 0.10  # OPTIMIZED: Only exclude top 10% (sky) for maximum vehicle detection
        return centroid[1] > height_threshold
    
    def _filter_detections_by_roi(self, detections: List[Dict], frame: np.ndarray) -> List[Dict]:
        """
        Filter detections to only include those within the region of interest
        
        Args:
            detections: List of detection dictionaries
            frame: Current video frame
            
        Returns:
            Filtered list of detections within ROI
        """
        filtered_detections = []
        
        for detection in detections:
            if self._is_in_roi(detection['centroid'], frame.shape[:2]):
                filtered_detections.append(detection)
        
        logger.debug(f"ROI filtering: {len(detections)} -> {len(filtered_detections)} detections")
        return filtered_detections
        
    def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract comprehensive video metadata"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Get file size
        file_size = os.path.getsize(video_path)
        
        # Get format info
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        
        cap.release()
        
        return {
            'duration': duration,
            'fps': fps,
            'total_frames': frame_count,
            'resolution': [width, height],
            'file_size': file_size,
            'format': Path(video_path).suffix.lower(),
            'codec': codec,
            'bitrate': int(file_size * 8 / duration) if duration > 0 else 0
        }
        
    
    def _multi_scale_detection(self, frame: np.ndarray) -> List[Dict]:
        """
        Multi-scale detection to catch vehicles at different distances
        """
        all_detections = []
        h, w = frame.shape[:2]
        
        try:
            # Original scale
            results_original = self.model(frame, conf=0.05, verbose=False)
            
            # Smaller scale for distant vehicles
            small_frame = cv2.resize(frame, (int(w*0.8), int(h*0.8)))
            results_small = self.model(small_frame, conf=0.04, verbose=False)
            
            # Process original scale results
            for result in results_original:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        if class_id in self.class_mapping:
                            confidence = float(box.conf[0])
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            detection = {
                                'class': self.class_mapping[class_id],
                                'confidence': confidence,
                                'bbox': [x1, y1, x2, y2],
                                'scale': 'original'
                            }
                            all_detections.append(detection)
            
            # Process small scale results (scale coordinates back)
            scale_x, scale_y = w / (w*0.8), h / (h*0.8)
            for result in results_small:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        if class_id in self.class_mapping:
                            confidence = float(box.conf[0])
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            # Scale coordinates back to original size
                            x1, x2 = x1 * scale_x, x2 * scale_x
                            y1, y2 = y1 * scale_y, y2 * scale_y
                            
                            detection = {
                                'class': self.class_mapping[class_id],
                                'confidence': confidence,
                                'bbox': [x1, y1, x2, y2],
                                'scale': 'small'
                            }
                            all_detections.append(detection)
            
            return all_detections
            
        except Exception as e:
            logger.warning(f"Multi-scale detection failed: {e}")
            return []

    def detect_vehicles_in_frame(self, frame: np.ndarray, frame_number: int, timestamp: float) -> Dict[str, Any]:
        """Detect vehicles in a single frame with improved accuracy and reduced false positives"""
        start_time = time.time()
        
        try:
            # Run YOLO detection with multiple confidence levels for better accuracy
            results = self.model(frame, conf=0.05, verbose=False)  # OPTIMIZED: 0.05 confidence for sweet spot detection
            
            detections = []
            vehicle_counts = defaultdict(int)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Check if it's a vehicle class
                        if class_id in self.class_mapping:
                            vehicle_class = self.class_mapping[class_id]
                            
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            
                            # IMPROVED: Validate detection quality to reduce false positives
                            box_width = x2 - x1
                            box_height = y2 - y1
                            box_area = box_width * box_height
                            aspect_ratio = box_width / max(box_height, 1)
                            
                            # ENHANCED: Smart quality filtering to reduce false positives while keeping real vehicles
                            frame_area = frame.shape[0] * frame.shape[1]
                            
                            # OPTIMIZED: Relaxed vehicle-specific area constraints for more detection
                            if vehicle_class == 'car':
                                min_area = 120   # RELAXED: Allow smaller cars (distant)
                                max_area = frame_area * 0.3   # RELAXED: Allow larger cars
                                min_aspect_ratio = 0.3  # RELAXED: More flexible ratios
                                max_aspect_ratio = 5.0
                            elif vehicle_class in ['truck', 'bus']:
                                min_area = 200   # RELAXED: Allow smaller trucks/buses (distant)
                                max_area = frame_area * 0.5   # RELAXED: Allow very large vehicles
                                min_aspect_ratio = 0.2  # RELAXED: More flexible for long vehicles
                                max_aspect_ratio = 8.0
                            elif vehicle_class in ['motorcycle', 'bicycle']:
                                min_area = 50    # RELAXED: Allow very small 2-wheelers
                                max_area = frame_area * 0.2   # RELAXED: Allow larger 2-wheelers
                                min_aspect_ratio = 0.1  # RELAXED: Very flexible for thin vehicles
                                max_aspect_ratio = 10.0   # RELAXED: Very long side views
                            else:
                                min_area = 80    # RELAXED: Lower minimum
                                max_area = frame_area * 0.4  # RELAXED: Higher maximum
                                min_aspect_ratio = 0.2
                                max_aspect_ratio = 8.0
                            
                            # Enhanced position validation - vehicles should be on ground level
                            centroid_y = (y1 + y2) / 2
                            frame_height = frame.shape[0]
                            
                            # Vehicles in top 20% of image are likely false positives (sky/buildings)
                            if centroid_y < frame_height * 0.2:
                                continue  # Skip detections in sky area
                            
                            # Skip detections that don't meet quality criteria
                            if (box_area < min_area or box_area > max_area or 
                                aspect_ratio < min_aspect_ratio or aspect_ratio > max_aspect_ratio):
                                continue
                            
                            # OPTIMIZED: Sweet spot confidence thresholds - maximum real vehicles, minimal false positives
                            min_confidence_by_class = {
                                'car': 0.08,       # OPTIMIZED: Lower for more car detection
                                'truck': 0.10,     # OPTIMIZED: Lower for more truck detection
                                'bus': 0.10,       # OPTIMIZED: Lower for more bus detection  
                                'motorcycle': 0.05, # OPTIMIZED: Much lower for 2-wheelers
                                'bicycle': 0.05    # OPTIMIZED: Much lower for 2-wheelers
                            }
                            
                            required_confidence = min_confidence_by_class.get(vehicle_class, 0.08)  # OPTIMIZED: Sweet spot threshold
                            if confidence < required_confidence:
                                continue
                            
                            # Calculate centroid
                            centroid = [(x1 + x2) / 2, (y1 + y2) / 2]
                            
                            detection = {
                                'class': vehicle_class,
                                'confidence': confidence,
                                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                'centroid': centroid,
                                'area': float(box_area),
                                'aspect_ratio': float(aspect_ratio)
                            }
                            
                            detections.append(detection)
            
            # 🎯 APPLY ROI FILTERING - Only if enabled (can be disabled for dense traffic)
            if self.enable_roi_filtering:
                detections = self._filter_detections_by_roi(detections, frame)
                logger.debug(f"ROI filtering applied: {len(detections)} detections after filtering")
            else:
                logger.debug(f"ROI filtering disabled: keeping all {len(detections)} detections")
            
            # Count vehicles after all filtering
            for detection in detections:
                vehicle_counts[detection['class']] += 1
            
            # Update tracker with filtered detections
            tracking_results = self.tracker.update(detections)
            
            processing_time = time.time() - start_time
            
            # Calculate congestion metrics
            total_vehicles = sum(vehicle_counts.values())
            frame_area = frame.shape[0] * frame.shape[1]
            vehicle_area = sum(det['area'] for det in detections)
            area_coverage = vehicle_area / frame_area if frame_area > 0 else 0
            
            # Determine congestion level
            if total_vehicles == 0:
                congestion_level = 'low'
                congestion_index = 0.0
            elif total_vehicles <= 5:
                congestion_level = 'low'
                congestion_index = min(0.3, area_coverage * 2)
            elif total_vehicles <= 15:
                congestion_level = 'medium'
                congestion_index = min(0.7, 0.3 + area_coverage * 2)
            else:
                congestion_level = 'high'
                congestion_index = min(1.0, 0.7 + area_coverage)
            
            logger.debug(f"Frame {frame_number}: {total_vehicles} vehicles detected (after quality filtering)")
            
            return {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'vehicle_count': total_vehicles,
                'vehicle_counts': dict(vehicle_counts),
                'detections': detections,
                'tracking_results': tracking_results,
                'density_level': congestion_level,
                'congestion_index': congestion_index,
                'processing_time': processing_time,
                'area_coverage': area_coverage
            }
            
        except Exception as e:
            logger.error(f"Error detecting vehicles in frame {frame_number}: {e}")
            # Return empty result on error
            return {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'vehicle_count': 0,
                'vehicle_counts': {},
                'detections': [],
                'tracking_results': {},
                'density_level': 'low',
                'congestion_index': 0.0,
                'processing_time': time.time() - start_time,
                'area_coverage': 0.0
            }
        
    def analyze_video(self, video_path: str, sample_rate: int = None) -> Dict[str, Any]:
        """Analyze entire video with comprehensive metrics - optimized for any video format"""
        logger.info(f"Starting enhanced video analysis: {video_path}")
        
        try:
            # Extract video metadata
            video_metadata = self.extract_video_metadata(video_path)
            logger.info(f"Video metadata: {video_metadata}")
            
            # Auto-adjust sample rate based on video properties
            if sample_rate is None:
                fps = video_metadata.get('fps', 30)
                duration = video_metadata.get('duration', 0)
                
                # Adaptive sampling optimized for maximum vehicle detection
                if fps > 60:
                    sample_rate = 2  # Very high FPS - sample every 2nd frame (optimized from 3)
                elif fps > 40:
                    sample_rate = 1  # High FPS - sample every frame (optimized from 2)
                elif fps > 25:
                    sample_rate = 1  # Normal FPS - sample every frame (optimized)
                else:
                    sample_rate = 1  # Low FPS - sample every frame
                
                # For dense traffic, reduce sampling even for long videos
                if duration > 30:
                    sample_rate = max(sample_rate, 1)  # Longer videos (optimized from 2)
                elif duration > 60:
                    sample_rate = max(sample_rate, 2)  # Very long videos (optimized from 3)
                
                logger.info(f"Auto-adjusted sample rate to {sample_rate} for FPS={fps:.1f}, duration={duration:.1f}s")
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            # Get actual video properties from OpenCV (more reliable)
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            actual_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Update metadata with actual values
            video_metadata.update({
                'fps': actual_fps if actual_fps > 0 else video_metadata.get('fps', 30),
                'frame_count': actual_frame_count if actual_frame_count > 0 else video_metadata.get('frame_count', 0),
                'width': actual_width if actual_width > 0 else video_metadata.get('width', 1280),
                'height': actual_height if actual_height > 0 else video_metadata.get('height', 720)
            })
            
            logger.info(f"Actual video properties: {actual_width}x{actual_height} @ {actual_fps:.1f}fps, {actual_frame_count} frames")
            
            frame_analyses = []
            vehicle_tracks = defaultdict(lambda: {
                'positions': [],
                'confidence_scores': [],
                'first_frame': None,
                'last_frame': None,
                'vehicle_class': None
            })
            
            frame_number = 0
            total_processing_time = 0
            frames_processed = 0
            max_frames_to_process = 500  # Limit for very long videos
            
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Stop processing if we've hit the frame limit (for very long videos)
                    if frames_processed >= max_frames_to_process:
                        logger.info(f"Reached maximum frame processing limit ({max_frames_to_process})")
                        break
                    
                    # Sample frames based on sample_rate
                    if frame_number % sample_rate == 0:
                        timestamp = frame_number / video_metadata['fps']
                        
                        try:
                            # Analyze frame with error handling
                            frame_analysis = self.detect_vehicles_in_frame(frame, frame_number, timestamp)
                            frame_analyses.append(frame_analysis)
                            frames_processed += 1
                            
                            total_processing_time += frame_analysis['processing_time']
                            
                            # Update vehicle tracks
                            for track_id, detection in frame_analysis['tracking_results'].items():
                                track = vehicle_tracks[track_id]
                                
                                if track['first_frame'] is None:
                                    track['first_frame'] = frame_number
                                    track['vehicle_class'] = detection['class']
                                
                                track['last_frame'] = frame_number
                                track['positions'].append(detection['centroid'])
                                track['confidence_scores'].append(detection['confidence'])
                        
                        except Exception as frame_error:
                            logger.warning(f"Error processing frame {frame_number}: {frame_error}")
                            # Continue with next frame instead of failing completely
                            continue
                            track['speeds'].append(speed)
                    
                    frame_number += 1
                    
                    # Progress logging
                    if frame_number % 100 == 0:
                        progress = (frame_number / video_metadata['total_frames']) * 100
                        logger.info(f"Processing progress: {progress:.1f}% ({frames_processed} frames analyzed)")
            
            finally:
                cap.release()
            
            logger.info(f"Completed frame processing: {frames_processed} frames analyzed")
            
            # Calculate comprehensive metrics
            metrics = self._calculate_comprehensive_metrics(frame_analyses, vehicle_tracks, video_metadata, total_processing_time)
            
            # Prepare vehicle tracks for storage
            formatted_tracks = []
            for track_id, track_data in vehicle_tracks.items():
                if track_data['positions']:  # Only include tracks with data
                    formatted_track = {
                        'track_id': track_id,
                        'vehicle_class': track_data['vehicle_class'],
                        'first_frame': track_data['first_frame'],
                        'last_frame': track_data['last_frame'],
                        'positions': track_data['positions'],
                        'confidence_scores': track_data['confidence_scores'],
                        'avg_confidence': np.mean(track_data['confidence_scores']) if track_data['confidence_scores'] else 0.0
                    }
                    formatted_tracks.append(formatted_track)
            
            logger.info(f"Video analysis completed. Processed {len(frame_analyses)} frames, tracked {len(formatted_tracks)} vehicles")
            
            # Generate annotated video with improved error handling
            annotated_video_path = None
            try:
                import tempfile
                import os
                
                # Create output path for annotated video
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                temp_dir = tempfile.gettempdir()
                annotated_video_path = os.path.join(temp_dir, f"annotated_{video_name}_{int(time.time())}.mp4")
                
                logger.info(f"🎯 Generating annotated video: {annotated_video_path}")
                logger.info(f"📊 Frame analyses available: {len(frame_analyses)}")
                
                # Check if we have frame analyses to work with
                if not frame_analyses:
                    logger.warning("⚠️ No frame analyses available for annotation, creating basic annotated video")
                    # Create a basic annotated video without detections
                    self.create_annotated_video(video_path, annotated_video_path, [])
                else:
                    # Create annotated video with detections
                    self.create_annotated_video(video_path, annotated_video_path, frame_analyses)
                
                # Verify the annotated video was created successfully
                if os.path.exists(annotated_video_path):
                    file_size = os.path.getsize(annotated_video_path)
                    if file_size > 0:
                        logger.info(f"✅ Annotated video generated successfully: {annotated_video_path} ({file_size / (1024*1024):.1f} MB)")
                    else:
                        logger.error(f"❌ Annotated video file is empty: {annotated_video_path}")
                        annotated_video_path = None
                else:
                    logger.error(f"❌ Annotated video file was not created: {annotated_video_path}")
                    annotated_video_path = None
                
            except Exception as e:
                logger.error(f"❌ Failed to generate annotated video: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Try to create a simple annotated video as fallback
                try:
                    logger.info("🔄 Attempting fallback annotated video creation...")
                    fallback_path = os.path.join(temp_dir, f"fallback_annotated_{video_name}_{int(time.time())}.mp4")
                    
                    # Create simple annotated video with just metrics overlay (no detections)
                    self.create_simple_annotated_video(video_path, fallback_path)
                    
                    if os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 0:
                        annotated_video_path = fallback_path
                        logger.info(f"✅ Fallback annotated video created: {annotated_video_path}")
                    else:
                        logger.error("❌ Fallback annotated video creation also failed")
                        annotated_video_path = None
                        
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback annotated video creation failed: {fallback_error}")
                    annotated_video_path = None
            
            return {
                'success': True,
                'video_metadata': video_metadata,
                'frame_analyses': frame_analyses,
                'vehicle_tracks': formatted_tracks,
                'traffic_metrics': metrics,
                'total_processing_time': total_processing_time,
                'annotated_video_path': annotated_video_path,
                'total_frames_analyzed': len(frame_analyses),
                'total_vehicles_detected': sum(f.get('vehicle_count', 0) for f in frame_analyses),
                'average_vehicles_per_frame': np.mean([f.get('vehicle_count', 0) for f in frame_analyses]) if frame_analyses else 0
            }
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return minimal result on error
            return {
                'success': False,
                'error': str(e),
                'video_metadata': {'duration': 0, 'fps': 0, 'total_frames': 0, 'resolution': [0, 0], 'file_size': 0, 'format': ''},
                'frame_analyses': [],
                'vehicle_tracks': [],
                'traffic_metrics': {},
                'total_processing_time': 0,
                'total_frames_analyzed': 0,
                'total_vehicles_detected': 0,
                'average_vehicles_per_frame': 0
            }
    
    def _calculate_comprehensive_metrics(self, frame_analyses: List[Dict], vehicle_tracks: Dict, 
                                       video_metadata: Dict, total_processing_time: float) -> Dict[str, Any]:
        """Calculate comprehensive traffic metrics"""
        if not frame_analyses:
            return {}
        
        # Vehicle count metrics
        vehicle_counts = [frame['vehicle_count'] for frame in frame_analyses]
        avg_vehicle_count = np.mean(vehicle_counts)
        max_vehicle_count = max(vehicle_counts)
        min_vehicle_count = min(vehicle_counts)
        
        # Find peak congestion time
        peak_frame_idx = np.argmax(vehicle_counts)
        peak_congestion_time = frame_analyses[peak_frame_idx]['timestamp']
        
        # Traffic flow metrics
        total_unique_vehicles = len(vehicle_tracks)
        video_duration_minutes = video_metadata['duration'] / 60
        vehicles_per_minute = total_unique_vehicles / video_duration_minutes if video_duration_minutes > 0 else 0
        
        # Congestion analysis
        high_congestion_frames = [f for f in frame_analyses if f['congestion_index'] > 0.7]
        congestion_duration = len(high_congestion_frames) * (video_metadata['fps'] / len(frame_analyses)) if frame_analyses else 0
        congestion_percentage = (len(high_congestion_frames) / len(frame_analyses)) * 100 if frame_analyses else 0
        
        # Traffic buildup rate
        if len(vehicle_counts) > 1:
            buildup_rates = []
            for i in range(1, len(vehicle_counts)):
                time_diff = frame_analyses[i]['timestamp'] - frame_analyses[i-1]['timestamp']
                count_diff = vehicle_counts[i] - vehicle_counts[i-1]
                if time_diff > 0:
                    buildup_rates.append(count_diff / (time_diff / 60))  # vehicles per minute
            traffic_buildup_rate = np.mean(buildup_rates) if buildup_rates else 0.0
        else:
            traffic_buildup_rate = 0.0
        
        # Performance metrics
        avg_processing_fps = len(frame_analyses) / total_processing_time if total_processing_time > 0 else 0
        
        # Detection accuracy (simplified - based on confidence scores)
        all_confidences = []
        for frame in frame_analyses:
            for detection in frame['detections']:
                all_confidences.append(detection['confidence'])
        detection_accuracy = np.mean(all_confidences) if all_confidences else 0.0
        
        return {
            'avg_vehicle_count': float(avg_vehicle_count),
            'max_vehicle_count': int(max_vehicle_count),
            'min_vehicle_count': int(min_vehicle_count),
            'peak_congestion_time': float(peak_congestion_time),
            'vehicles_per_minute': float(vehicles_per_minute),
            'congestion_duration': float(congestion_duration),
            'congestion_percentage': float(congestion_percentage),
            'traffic_buildup_rate': float(traffic_buildup_rate),
            'avg_processing_fps': float(avg_processing_fps),
            'total_processing_time': float(total_processing_time),
            'detection_accuracy': float(detection_accuracy)
        }
    
    def create_annotated_video(self, video_path: str, output_path: str, frame_analyses: List[Dict]) -> str:
        """Create annotated video with bounding boxes and metrics - optimized for browser compatibility"""
        logger.info(f"🎯 Creating annotated video: {output_path}")
        logger.info(f"📊 Frame analyses count: {len(frame_analyses)}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Force browser-compatible settings for high FPS videos
        target_fps = 30.0 if original_fps > 40 else original_fps
        
        # Ensure valid FPS
        if target_fps <= 0 or target_fps > 120:
            target_fps = 30.0
            logger.warning(f"Invalid FPS detected, using fallback: {target_fps}")
        
        if original_fps > 40:
            logger.info(f"High FPS detected ({original_fps:.1f}), reducing to {target_fps} for browser compatibility")
        
        # Ensure dimensions are even numbers (required for codecs)
        if width % 2 != 0:
            width -= 1
        if height % 2 != 0:
            height -= 1
        
        logger.info(f"📹 Video properties: {width}x{height} @ {target_fps:.1f}fps (original: {original_fps:.1f}fps)")
        
        # Ensure output path has proper extension
        if not output_path.lower().endswith('.mp4'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp4'
            logger.info(f"🔧 Changed output extension to .mp4 for browser compatibility: {output_path}")
        
        # Use browser-compatible codec - H.264 works best across all browsers
        logger.info(f"🔧 Using H.264 codec for maximum browser compatibility")
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        
        # Create video writer
        out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height), True)
        
        if not out.isOpened():
            # Fallback to mp4v if H.264 fails
            logger.warning("H.264 codec failed, falling back to mp4v")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height), True)
            
            if not out.isOpened():
                # Final fallback to XVID
                logger.warning("mp4v codec failed, falling back to XVID")
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                output_path = output_path.rsplit('.', 1)[0] + '.avi'  # Change to AVI for XVID
                out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height), True)
                
                if not out.isOpened():
                    cap.release()
                    raise ValueError(f"Could not create output video file with any codec: {output_path}")
        
        logger.info(f"🎬 Using codec: {fourcc} for video creation")
        
        frame_number = 0
        analysis_idx = 0
        frames_written = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame skipping for FPS reduction (high FPS videos)
        frame_skip_ratio = original_fps / target_fps if original_fps > 40 else 1.0
        if frame_skip_ratio > 1:
            logger.info(f"Frame skipping ratio: {frame_skip_ratio:.2f} (will keep ~{1/frame_skip_ratio:.1%} of frames)")
        
        logger.info(f"📊 Processing {total_frames} frames for annotation")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # FPS reduction: Skip frames for high FPS videos (browser compatibility)
                if frame_skip_ratio > 1:
                    # Skip frames to achieve target FPS: for 50fps->30fps, keep every ~1.67th frame
                    should_skip = (frame_number % int(frame_skip_ratio + 0.5)) == 1
                    if should_skip:
                        frame_number += 1
                        continue  # Skip this frame
                
                # Resize frame if needed to match output dimensions
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                
                # Find corresponding analysis
                current_analysis = None
                if analysis_idx < len(frame_analyses):
                    # Look for analysis that matches this frame
                    for i in range(analysis_idx, len(frame_analyses)):
                        if frame_analyses[i].get('frame_number', i) == frame_number:
                            current_analysis = frame_analyses[i]
                            analysis_idx = i + 1
                            break
                
                # Always draw metrics overlay, even if no detections
                metrics_text = []
                if current_analysis:
                    # Draw bounding boxes if detections exist
                    detections = current_analysis.get('detections', [])
                    
                    # LIMIT DETECTIONS FOR PERFORMANCE - Only show top detections when there are too many
                    MAX_ANNOTATIONS = 50  # Increased limit for better visibility
                    if len(detections) > MAX_ANNOTATIONS:
                        # Sort by confidence and take top detections
                        detections = sorted(detections, key=lambda x: x.get('confidence', 0), reverse=True)[:MAX_ANNOTATIONS]
                        logger.info(f"Limited video annotations to top {MAX_ANNOTATIONS} detections (out of {len(current_analysis.get('detections', []))} total)")
                    
                    for detection in detections:
                        try:
                            bbox = detection.get('bbox', [])
                            if len(bbox) >= 4:
                                x1, y1, x2, y2 = bbox[:4]
                                confidence = detection.get('confidence', 0.0)
                                vehicle_class = detection.get('class', 'vehicle')
                                
                                # Ensure coordinates are within frame bounds
                                x1 = max(0, min(int(x1), width - 1))
                                y1 = max(0, min(int(y1), height - 1))
                                x2 = max(0, min(int(x2), width - 1))
                                y2 = max(0, min(int(y2), height - 1))
                                
                                # Only draw if bounding box is valid and has reasonable size
                                if x2 > x1 and y2 > y1 and (x2 - x1) > 5 and (y2 - y1) > 5:
                                    # Choose color based on grouped vehicle category
                                    colors = {
                                        'car': (0, 255, 0),           # Green for Cars
                                        'truck': (255, 0, 0),         # Blue for Large Vehicles
                                        'bus': (255, 0, 0),           # Blue for Large Vehicles  
                                        'motorcycle': (255, 255, 0),  # Cyan for 2-Wheelers
                                        'bicycle': (255, 255, 0)      # Cyan for 2-Wheelers (same as motorcycle)
                                    }
                                    color = colors.get(vehicle_class, (0, 255, 0))
                                    
                                    # Draw bounding box with thicker lines for better visibility
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                                    
                                    # Map individual classes to grouped categories for display
                                    class_mapping = {
                                        'car': 'Car',
                                        'truck': 'Large Vehicle', 
                                        'bus': 'Large Vehicle',
                                        'motorcycle': '2-Wheeler',
                                        'bicycle': '2-Wheeler'
                                    }
                                    
                                    # Use grouped class name for label
                                    display_class = class_mapping.get(vehicle_class, vehicle_class.title())
                                    
                                    # Draw label with grouped class name
                                    label = f"{display_class}: {confidence:.2f}"
                                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                                    
                                    # Draw label background
                                    cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                                (x1 + label_size[0] + 10, y1), color, -1)
                                    
                                    # Draw label text in white
                                    cv2.putText(frame, label, (x1 + 5, y1 - 5), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        except Exception as e:
                            logger.warning(f"Error drawing detection: {e}")
                    
                    # Calculate vehicle counts by type for this frame
                    vehicle_counts_by_type = {}
                    for detection in current_analysis.get('detections', []):
                        vehicle_class = detection.get('class', 'vehicle')
                        vehicle_counts_by_type[vehicle_class] = vehicle_counts_by_type.get(vehicle_class, 0) + 1
                    
                    # Show detection summary if limited
                    total_detections = len(current_analysis.get('detections', []))
                    if total_detections > len(detections):
                        # Prepare metrics text with detection summary
                        metrics_text = [
                            f"Frame: {frame_number}",
                            f"Total Vehicles: {current_analysis.get('vehicle_count', 0)}",
                            f"Cars: {vehicle_counts_by_type.get('car', 0)}",
                            f"Trucks/Buses: {vehicle_counts_by_type.get('truck', 0) + vehicle_counts_by_type.get('bus', 0)}",
                            f"2-Wheelers: {vehicle_counts_by_type.get('motorcycle', 0) + vehicle_counts_by_type.get('bicycle', 0)}"
                        ]
                    else:
                        # Prepare normal metrics text with vehicle type breakdown
                        metrics_text = [
                            f"Frame: {frame_number}",
                            f"Total Vehicles: {current_analysis.get('vehicle_count', 0)}",
                            f"Cars: {vehicle_counts_by_type.get('car', 0)}",
                            f"Trucks/Buses: {vehicle_counts_by_type.get('truck', 0) + vehicle_counts_by_type.get('bus', 0)}",
                            f"2-Wheelers: {vehicle_counts_by_type.get('motorcycle', 0) + vehicle_counts_by_type.get('bicycle', 0)}"
                        ]
                else:
                    # Default metrics when no analysis available
                    metrics_text = [
                        f"Frame: {frame_number}",
                        f"Total Vehicles: 0",
                        f"Cars: 0",
                        f"Trucks/Buses: 0",
                        f"2-Wheelers: 0"
                    ]
                
                # Draw enhanced metrics overlay with better styling and centered positioning
                overlay_height = len(metrics_text) * 30 + 20
                overlay_width = 350
                
                # Center the overlay both horizontally and vertically on the frame
                frame_height = frame.shape[0]
                frame_width = frame.shape[1]
                overlay_x = (frame_width - overlay_width) // 2
                overlay_y = (frame_height - overlay_height) // 2
                
                # Draw semi-transparent background
                overlay = frame.copy()
                cv2.rectangle(overlay, (overlay_x, overlay_y), (overlay_x + overlay_width, overlay_y + overlay_height), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
                
                # Draw border
                cv2.rectangle(frame, (overlay_x, overlay_y), (overlay_x + overlay_width, overlay_y + overlay_height), (255, 255, 255), 2)
                
                # Draw metrics text centered in the overlay
                for i, text in enumerate(metrics_text):
                    # Calculate text size for centering
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    text_x = overlay_x + (overlay_width - text_size[0]) // 2
                    text_y = overlay_y + 30 + i * 30
                    
                    cv2.putText(frame, text, (text_x, text_y), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Write frame to output video
                # Note: On some Windows systems, out.write() may return False even when successful
                # We'll write the frame and verify success by checking the output file
                try:
                    # Ensure frame is in correct format and contiguous in memory
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        # Make sure frame is contiguous and uint8
                        frame = np.ascontiguousarray(frame, dtype=np.uint8)
                        
                        # Write the frame (ignore return value as it may be unreliable on Windows)
                        out.write(frame)
                        frames_written += 1  # Count all attempted writes
                    else:
                        logger.warning(f"Frame {frame_number} has incorrect shape: {frame.shape}")
                except Exception as write_error:
                    logger.warning(f"Error writing frame {frame_number}: {write_error}")
                    # Continue processing even if one frame fails
                
                frame_number += 1
                
                # Progress logging for long videos
                if frame_number % 100 == 0:
                    progress = (frame_number / max(total_frames, 1)) * 100
                    logger.info(f"Annotation progress: {progress:.1f}% ({frames_written} frames written)")
        
        except Exception as e:
            logger.error(f"Error during video annotation: {e}")
            raise
        
        finally:
            cap.release()
            if out:
                out.release()
        
        # Verify the output file was created and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 0:
                logger.info(f"✅ Annotated video created successfully: {frames_written} frames written")
                logger.info(f"📊 Output file: {output_path} ({file_size / (1024*1024):.1f} MB)")
                logger.info(f"🎬 Codec used: mp4v")
                
                # Additional verification - try to read the video
                try:
                    verify_cap = cv2.VideoCapture(output_path)
                    if verify_cap.isOpened():
                        verify_fps = verify_cap.get(cv2.CAP_PROP_FPS)
                        verify_frames = int(verify_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        verify_cap.release()
                        logger.info(f"✅ Video verification: {verify_frames} frames @ {verify_fps:.1f}fps")
                    else:
                        logger.warning("⚠️ Created video cannot be opened for verification")
                except Exception as verify_error:
                    logger.warning(f"⚠️ Video verification failed: {verify_error}")
                
                return output_path
            else:
                logger.error(f"❌ Output video file is empty: {output_path}")
                raise ValueError(f"Generated video file is empty: {output_path}")
        else:
            logger.error(f"❌ Output video file was not created: {output_path}")
            raise ValueError(f"Failed to create output video file: {output_path}")
    
    def create_simple_annotated_video(self, video_path: str, output_path: str) -> str:
        """Create a simple annotated video with just metrics overlay (fallback method)"""
        logger.info(f"🎯 Creating simple annotated video: {output_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Ensure valid FPS
        if fps <= 0 or fps > 120:
            fps = 30.0
        
        # Ensure dimensions are even
        if width % 2 != 0:
            width -= 1
        if height % 2 != 0:
            height -= 1
        
        # Ensure output path has .mp4 extension
        if not output_path.lower().endswith('.mp4'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp4'
        
        # Use mp4v codec (best browser compatibility for Windows 10)
        # Try H.264 first for better browser compatibility
        codec_options = [
            ('avc1', cv2.VideoWriter_fourcc(*'avc1')),  # H.264 - best browser support
            ('H264', cv2.VideoWriter_fourcc(*'H264')),  # H.264 - alternative
            ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),  # MPEG-4 fallback
        ]
        
        out = None
        successful_codec = None
        
        for codec_name, fourcc in codec_options:
            try:
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)
                if out.isOpened():
                    successful_codec = codec_name
                    logger.info(f"✅ Using codec: {codec_name} for simple video")
                    break
                else:
                    if out:
                        out.release()
                    out = None
            except Exception as e:
                logger.warning(f"❌ Codec {codec_name} failed: {e}")
                if out:
                    out.release()
                out = None
        
        if not out or not out.isOpened():
            cap.release()
            raise ValueError(f"Could not create simple output video file with any codec: {output_path}")
        
        logger.info(f"🎬 Using codec: {successful_codec} for simple MP4 video creation")
        
        frame_number = 0
        frames_written = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame if needed
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                
                # Add simple metrics overlay
                metrics_text = [
                    f"Frame: {frame_number}",
                    f"Status: Processing",
                    f"Analysis: Complete",
                    f"Mode: Simple View"
                ]
                
                # Draw enhanced metrics overlay
                overlay_height = len(metrics_text) * 30 + 20
                overlay_width = 300
                
                # Semi-transparent background
                overlay = frame.copy()
                cv2.rectangle(overlay, (10, 10), (overlay_width, overlay_height), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
                
                # Border
                cv2.rectangle(frame, (10, 10), (overlay_width, overlay_height), (255, 255, 255), 2)
                
                # Text
                for i, text in enumerate(metrics_text):
                    cv2.putText(frame, text, (20, 40 + i * 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Write frame
                try:
                    success = out.write(frame)
                    if success:
                        frames_written += 1
                except Exception as e:
                    logger.warning(f"Error writing simple frame {frame_number}: {e}")
                
                frame_number += 1
                
                # Limit to first 100 frames for fallback
                if frame_number >= 100:
                    break
        
        finally:
            cap.release()
            if out:
                out.release()
        
        logger.info(f"✅ Simple annotated video created: {frames_written} frames written")
        return output_path