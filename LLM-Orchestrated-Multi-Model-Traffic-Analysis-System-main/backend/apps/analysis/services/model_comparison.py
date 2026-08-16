"""
Model Comparison Service for YOLOv8 vs YOLOv12
"""
import time
import numpy as np
from typing import Dict, List, Any, Tuple
import logging
from .yolov8_analyzer import YOLOv8TrafficAnalyzer
from .yolov12_analyzer import YOLOv12TrafficAnalyzer

logger = logging.getLogger(__name__)


class ModelComparisonService:
    """
    Service to compare YOLOv8 and YOLOv12 model performance
    """
    
    def __init__(self):
        """Initialize both analyzers"""
        self.yolov8_analyzer = YOLOv8TrafficAnalyzer()
        self.yolov12_analyzer = YOLOv12TrafficAnalyzer()
    
    def compare_models(self, image_path: str) -> Dict[str, Any]:
        """
        Compare both models on the same image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing comparison results
        """
        start_time = time.time()
        
        try:
            # Run analysis with both models
            yolov8_results = self.yolov8_analyzer.analyze_traffic_scene(image_path)
            yolov12_results = self.yolov12_analyzer.analyze_traffic_scene(image_path)
            
            # Extract key metrics for comparison
            comparison_metrics = self._calculate_comparison_metrics(yolov8_results, yolov12_results)
            
            # Determine best model
            best_model = self._select_best_model(comparison_metrics)
            
            # Create consolidated result
            consolidated_result = self._create_consolidated_result(
                yolov8_results, yolov12_results, best_model
            )
            
            total_time = time.time() - start_time
            
            return {
                'yolov8_results': yolov8_results,
                'yolov12_results': yolov12_results,
                'comparison_metrics': comparison_metrics,
                'best_model': best_model,
                'consolidated_result': consolidated_result,
                'comparison_time': total_time
            }
            
        except Exception as e:
            logger.error(f"Error in model comparison: {e}")
            return {
                'error': str(e),
                'yolov8_results': {},
                'yolov12_results': {},
                'comparison_metrics': {},
                'best_model': 'unknown',
                'consolidated_result': {}
            }
    
    def _calculate_comparison_metrics(self, yolov8_results: Dict[str, Any], yolov12_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comparison metrics between the two models
        
        Args:
            yolov8_results: YOLOv8 analysis results
            yolov12_results: YOLOv12 analysis results
            
        Returns:
            Dictionary containing comparison metrics
        """
        try:
            # Extract detection data
            yolov8_detection = yolov8_results.get('vehicle_detection', {})
            yolov12_detection = yolov12_results.get('vehicle_detection', {})
            
            yolov8_performance = yolov8_results.get('performance_metrics', {})
            yolov12_performance = yolov12_results.get('performance_metrics', {})
            
            # Vehicle count comparison
            yolov8_count = yolov8_detection.get('total_vehicles', 0)
            yolov12_count = yolov12_detection.get('total_vehicles', 0)
            
            # Confidence comparison
            yolov8_confidence = yolov8_detection.get('average_confidence', 0)
            yolov12_confidence = yolov12_detection.get('average_confidence', 0)
            
            # Performance comparison
            yolov8_fps = yolov8_performance.get('fps', 0)
            yolov12_fps = yolov12_performance.get('fps', 0)
            
            yolov8_time = yolov8_performance.get('processing_time', 0)
            yolov12_time = yolov12_performance.get('processing_time', 0)
            
            # Calculate differences
            count_difference = abs(yolov8_count - yolov12_count)
            confidence_difference = abs(yolov8_confidence - yolov12_confidence)
            fps_difference = abs(yolov8_fps - yolov12_fps)
            
            # Calculate accuracy scores (based on confidence and consistency)
            yolov8_accuracy = self._calculate_accuracy_score(yolov8_detection, yolov8_performance)
            yolov12_accuracy = self._calculate_accuracy_score(yolov12_detection, yolov12_performance)
            
            return {
                'detection_comparison': {
                    'yolov8_count': yolov8_count,
                    'yolov12_count': yolov12_count,
                    'count_difference': count_difference,
                    'count_agreement': count_difference <= 2  # Consider agreement if within 2 vehicles
                },
                'confidence_comparison': {
                    'yolov8_confidence': yolov8_confidence,
                    'yolov12_confidence': yolov12_confidence,
                    'confidence_difference': confidence_difference,
                    'higher_confidence': 'YOLOv8' if yolov8_confidence > yolov12_confidence else 'YOLOv12'
                },
                'performance_comparison': {
                    'yolov8_fps': yolov8_fps,
                    'yolov12_fps': yolov12_fps,
                    'yolov8_time': yolov8_time,
                    'yolov12_time': yolov12_time,
                    'faster_model': 'YOLOv8' if yolov8_fps > yolov12_fps else 'YOLOv12',
                    'fps_difference': fps_difference
                },
                'accuracy_scores': {
                    'yolov8_accuracy': yolov8_accuracy,
                    'yolov12_accuracy': yolov12_accuracy,
                    'more_accurate': 'YOLOv8' if yolov8_accuracy > yolov12_accuracy else 'YOLOv12'
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating comparison metrics: {e}")
            return {}
    
    def _calculate_accuracy_score(self, detection_results: Dict[str, Any], performance_metrics: Dict[str, Any]) -> float:
        """
        Calculate an accuracy score based on detection confidence and performance
        
        Args:
            detection_results: Detection results from a model
            performance_metrics: Performance metrics from a model
            
        Returns:
            Accuracy score between 0 and 1
        """
        try:
            # Base score from average confidence
            confidence_score = detection_results.get('average_confidence', 0)
            
            # Penalty for very low or very high detection counts (unrealistic)
            vehicle_count = detection_results.get('total_vehicles', 0)
            count_penalty = 0
            if vehicle_count == 0:
                count_penalty = 0.2  # Penalty for no detections
            elif vehicle_count > 50:
                count_penalty = 0.1  # Penalty for too many detections
            
            # Bonus for consistent detections (higher confidence variance is bad)
            detections = detection_results.get('detections', [])
            if detections:
                confidences = [det.get('confidence', 0) for det in detections]
                confidence_std = np.std(confidences) if len(confidences) > 1 else 0
                consistency_bonus = max(0, 0.1 - confidence_std)  # Bonus for low variance
            else:
                consistency_bonus = 0
            
            # Performance bonus (faster processing is better)
            fps = performance_metrics.get('fps', 0)
            performance_bonus = min(0.1, fps / 100)  # Small bonus for speed
            
            # Calculate final score
            accuracy_score = confidence_score - count_penalty + consistency_bonus + performance_bonus
            
            return max(0, min(1, accuracy_score))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating accuracy score: {e}")
            return 0.5  # Default middle score
    
    def _select_best_model(self, comparison_metrics: Dict[str, Any]) -> str:
        """
        Select the best performing model based on comparison metrics
        
        Args:
            comparison_metrics: Comparison metrics between models
            
        Returns:
            Name of the best model ('YOLOv8' or 'YOLOv12')
        """
        try:
            # Scoring system
            yolov8_score = 0
            yolov12_score = 0
            
            # Accuracy score (weight: 40%)
            accuracy_scores = comparison_metrics.get('accuracy_scores', {})
            yolov8_accuracy = accuracy_scores.get('yolov8_accuracy', 0)
            yolov12_accuracy = accuracy_scores.get('yolov12_accuracy', 0)
            
            if yolov8_accuracy > yolov12_accuracy:
                yolov8_score += 4
            elif yolov12_accuracy > yolov8_accuracy:
                yolov12_score += 4
            else:
                yolov8_score += 2
                yolov12_score += 2
            
            # Confidence score (weight: 30%)
            confidence_comparison = comparison_metrics.get('confidence_comparison', {})
            higher_confidence = confidence_comparison.get('higher_confidence', '')
            
            if higher_confidence == 'YOLOv8':
                yolov8_score += 3
            elif higher_confidence == 'YOLOv12':
                yolov12_score += 3
            
            # Performance score (weight: 20%)
            performance_comparison = comparison_metrics.get('performance_comparison', {})
            faster_model = performance_comparison.get('faster_model', '')
            
            if faster_model == 'YOLOv8':
                yolov8_score += 2
            elif faster_model == 'YOLOv12':
                yolov12_score += 2
            
            # Detection consistency (weight: 10%)
            detection_comparison = comparison_metrics.get('detection_comparison', {})
            count_agreement = detection_comparison.get('count_agreement', False)
            
            if count_agreement:
                # If both models agree, give slight preference to YOLOv12 (newer model)
                yolov12_score += 1
            else:
                # If they disagree, prefer the one with higher confidence
                if higher_confidence == 'YOLOv8':
                    yolov8_score += 1
                elif higher_confidence == 'YOLOv12':
                    yolov12_score += 1
            
            # Determine winner
            if yolov8_score > yolov12_score:
                return 'YOLOv8'
            elif yolov12_score > yolov8_score:
                return 'YOLOv12'
            else:
                return 'YOLOv12'  # Default to newer model in case of tie
                
        except Exception as e:
            logger.error(f"Error selecting best model: {e}")
            return 'YOLOv12'  # Default fallback
    
    def _create_consolidated_result(self, yolov8_results: Dict[str, Any], yolov12_results: Dict[str, Any], best_model: str) -> Dict[str, Any]:
        """
        Create a consolidated result using the best model's output
        
        Args:
            yolov8_results: YOLOv8 results
            yolov12_results: YOLOv12 results
            best_model: Name of the best performing model
            
        Returns:
            Consolidated analysis result
        """
        try:
            # Use the best model's results as the base
            if best_model == 'YOLOv8':
                base_results = yolov8_results
                alternative_results = yolov12_results
            else:
                base_results = yolov12_results
                alternative_results = yolov8_results
            
            # Extract key data
            base_detection = base_results.get('vehicle_detection', {})
            base_density = base_results.get('traffic_density', {})
            base_performance = base_results.get('performance_metrics', {})
            
            alt_detection = alternative_results.get('vehicle_detection', {})
            alt_density = alternative_results.get('traffic_density', {})
            
            # Create consolidated detection result
            consolidated_detection = base_detection.copy()
            
            # Add comparison data
            consolidated_detection['model_comparison'] = {
                'primary_model': best_model,
                'alternative_model': 'YOLOv8' if best_model == 'YOLOv12' else 'YOLOv12',
                'primary_count': base_detection.get('total_vehicles', 0),
                'alternative_count': alt_detection.get('total_vehicles', 0),
                'primary_confidence': base_detection.get('average_confidence', 0),
                'alternative_confidence': alt_detection.get('average_confidence', 0)
            }
            
            # Create consolidated density result
            consolidated_density = base_density.copy()
            consolidated_density['model_comparison'] = {
                'primary_density': base_density.get('density_level', 'Unknown'),
                'alternative_density': alt_density.get('density_level', 'Unknown'),
                'density_agreement': base_density.get('density_level') == alt_density.get('density_level')
            }
            
            # Enhanced performance metrics
            consolidated_performance = base_performance.copy()
            consolidated_performance['model_selection'] = {
                'selected_model': best_model,
                'selection_reason': f"Best overall performance based on accuracy, confidence, and speed",
                'comparison_available': True
            }
            
            return {
                'vehicle_detection': consolidated_detection,
                'traffic_density': consolidated_density,
                'performance_metrics': consolidated_performance,
                'annotated_image_path': base_results.get('annotated_image_path', ''),
                'model_comparison_summary': {
                    'models_compared': ['YOLOv8', 'YOLOv12'],
                    'selected_model': best_model,
                    'confidence_in_selection': 'High' if abs(base_detection.get('average_confidence', 0) - alt_detection.get('average_confidence', 0)) > 0.1 else 'Medium'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating consolidated result: {e}")
            return yolov12_results  # Fallback to YOLOv12 results