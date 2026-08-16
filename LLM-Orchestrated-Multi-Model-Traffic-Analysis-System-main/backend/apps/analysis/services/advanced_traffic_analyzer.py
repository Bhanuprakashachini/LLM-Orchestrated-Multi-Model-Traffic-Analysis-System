"""
Advanced Traffic Analyzer - Integration Service
Combines AI Processing Engine with Vehicle Detection
"""
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
import time
import json
from pathlib import Path

from .advanced_ai_engine import AdvancedAIEngine
from .yolov8_analyzer import YOLOv8TrafficAnalyzer

logger = logging.getLogger(__name__)


class AdvancedTrafficAnalyzer:
    """
    Comprehensive traffic analysis system integrating all advanced features
    """
    
    def __init__(self, device: str = 'auto', confidence_threshold: float = 0.4):
        """
        Initialize the advanced traffic analyzer
        
        Args:
            device: Device to use ('cpu', 'cuda', or 'auto')
            confidence_threshold: Minimum confidence for detections
        """
        self.device = device
        self.confidence_threshold = confidence_threshold
        
        # Initialize all components
        self.ai_engine = AdvancedAIEngine(device=device)
        self.vehicle_detector = YOLOv8TrafficAnalyzer(
            device=device, 
            confidence_threshold=confidence_threshold
        )
        
        # Analysis state
        self.current_frame = None
        self.analysis_history = []
        self.calibrated = False
        
        logger.info("Advanced Traffic Analyzer initialized with all features")
    
    def analyze_comprehensive(self, image_path: str, enable_all_features: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive traffic analysis with all advanced features
        
        Args:
            image_path: Path to the traffic image
            enable_all_features: Whether to enable all advanced features
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        start_time = time.time()
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            self.current_frame = image
            
            print("🚀 ADVANCED TRAFFIC ANALYSIS STARTING")
            print("=" * 60)
            
            # 1. Basic Vehicle Detection
            print("🔍 Step 1: Vehicle Detection...")
            vehicle_results = self.vehicle_detector.analyze_traffic_scene(image_path)
            
            # 2. AI Scene Context Analysis
            print("🧠 Step 2: AI Scene Analysis...")
            if enable_all_features:
                scene_context = self.ai_engine.analyze_scene_context(image)
            else:
                scene_context = {'scene_type': 'unknown', 'weather_condition': 'clear'}
            
            # 3. AI Insights Generation (Lane Analysis Removed)
            print("💡 Step 3: AI Insights...")
            if enable_all_features:
                combined_results = {
                    **vehicle_results,
                    **scene_context
                }
                ai_insights = self.ai_engine.generate_ai_insights(combined_results)
            else:
                ai_insights = {'key_findings': [], 'recommendations': []}
            
            # 4. Compile Comprehensive Results
            processing_time = time.time() - start_time
            
            comprehensive_results = {
                # Basic Analysis
                'vehicle_detection': {
                    'total_vehicles': vehicle_results.get('total_vehicles', 0),
                    'vehicle_counts': vehicle_results.get('vehicle_counts', {}),
                    'detections': vehicle_results.get('detections', []),
                    'average_confidence': vehicle_results.get('average_confidence', 0.0)
                },
                
                # AI Scene Analysis
                'scene_analysis': {
                    'scene_type': scene_context.get('scene_type', 'unknown'),
                    'weather_condition': scene_context.get('weather_condition', 'clear'),
                    'time_of_day': scene_context.get('time_of_day', 'unknown'),
                    'visibility_score': scene_context.get('visibility_score', 0.0),
                    'scene_complexity': scene_context.get('scene_complexity', 'medium'),
                    'lighting_quality': scene_context.get('lighting_quality', 'unknown')
                },
                
                # Lane Analysis (Feature Removed)
                'lane_analysis': {
                    'available': False,
                    'removed': True,
                    'message': 'Lane analysis feature has been removed per user request'
                },
                
                # AI Insights
                'ai_insights': {
                    'key_findings': ai_insights.get('key_findings', []),
                    'recommendations': ai_insights.get('recommendations', []),
                    'risk_assessment': ai_insights.get('risk_assessment', 'low'),
                    'optimization_suggestions': ai_insights.get('optimization_suggestions', []),
                    'confidence_score': ai_insights.get('confidence_score', 0.0)
                },
                
                # Enhanced Traffic Density
                'enhanced_traffic_density': self._calculate_enhanced_density(
                    vehicle_results, scene_context
                ),
                
                # Performance Metrics
                'performance_metrics': {
                    'processing_time': processing_time,
                    'fps': 1.0 / processing_time if processing_time > 0 else 0,
                    'features_enabled': {
                        'ai_processing': enable_all_features,
                        'lane_analysis': False,  # Feature removed
                        'basic_detection': True
                    },
                    'model_version': 'Advanced Traffic Analyzer v2.0',
                    'device_used': self.device
                },
                
                # Analysis Metadata
                'analysis_metadata': {
                    'image_path': image_path,
                    'image_dimensions': {
                        'width': image.shape[1],
                        'height': image.shape[0]
                    },
                    'analysis_timestamp': time.time(),
                    'features_used': [
                        'vehicle_detection',
                        'ai_scene_analysis' if enable_all_features else None,
                        'ai_insights' if enable_all_features else None
                    ]
                }
            }
            
            # Store in history
            self.analysis_history.append(comprehensive_results)
            
            print("✅ ADVANCED ANALYSIS COMPLETE")
            print(f"⏱️  Processing Time: {processing_time:.2f}s")
            print(f"🚗 Vehicles Detected: {comprehensive_results['vehicle_detection']['total_vehicles']}")
            print("=" * 60)
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error: {e}")
            return {
                'error': str(e),
                'processing_time': time.time() - start_time,
                'vehicle_detection': {'total_vehicles': 0},
                'scene_analysis': {},
                'lane_analysis': {'available': False, 'removed': True},
                'ai_insights': {'key_findings': [], 'recommendations': []}
            }
    
    def _calculate_enhanced_density(self, vehicle_results: Dict[str, Any], 
                                  scene_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate enhanced traffic density with AI context (lane analysis removed)"""
        total_vehicles = vehicle_results.get('total_vehicles', 0)
        # Use estimated lanes since lane detection was removed
        estimated_lanes = 2  # Default assumption for most roads
        scene_type = scene_context.get('scene_type', 'unknown')
        weather = scene_context.get('weather_condition', 'clear')
        
        # Base density calculation
        vehicles_per_lane = total_vehicles / max(estimated_lanes, 1)
        
        # Adjust based on scene type
        scene_multipliers = {
            'highway': 1.2,
            'urban_street': 1.0,
            'intersection': 1.5,
            'parking_lot': 0.8,
            'residential': 0.9
        }
        
        scene_multiplier = scene_multipliers.get(scene_type, 1.0)
        adjusted_density = vehicles_per_lane * scene_multiplier
        
        # Weather impact
        weather_multipliers = {
            'clear': 1.0,
            'cloudy': 1.1,
            'rainy': 1.3,
            'foggy': 1.4,
            'snowy': 1.5
        }
        
        weather_multiplier = weather_multipliers.get(weather, 1.0)
        final_density = adjusted_density * weather_multiplier
        
        # Classify density level
        if final_density < 1.0:
            density_level = 'Low'
            congestion_index = min(0.3, final_density / 1.0 * 0.3)
        elif final_density < 3.0:
            density_level = 'Medium'
            congestion_index = 0.3 + (final_density - 1.0) / 2.0 * 0.3
        elif final_density < 6.0:
            density_level = 'High'
            congestion_index = 0.6 + (final_density - 3.0) / 3.0 * 0.3
        else:
            density_level = 'Congested'
            congestion_index = min(1.0, 0.9 + (final_density - 6.0) / 6.0 * 0.1)
        
        return {
            'density_level': density_level,
            'congestion_index': round(congestion_index, 3),
            'vehicles_per_lane': round(vehicles_per_lane, 2),
            'adjusted_density': round(final_density, 2),
            'scene_impact': scene_multiplier,
            'weather_impact': weather_multiplier,
            'total_vehicles': total_vehicles,
            'estimated_lanes': estimated_lanes,
            'note': 'Lane detection removed - using estimated lane count'
        }
    
    def create_comprehensive_visualization(self, image_path: str, 
                                        analysis_results: Dict[str, Any]) -> np.ndarray:
        """
        Create comprehensive visualization with all analysis features
        
        Args:
            image_path: Path to original image
            analysis_results: Results from comprehensive analysis
            
        Returns:
            Annotated image with all visualizations
        """
        try:
            # Load original image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Create visualization layers
            annotated_image = image.copy()
            
            # 1. Vehicle Detection Visualization
            detections = analysis_results.get('vehicle_detection', {}).get('detections', [])
            for detection in detections:
                bbox = detection.get('bbox', {})
                vehicle_type = detection.get('class', 'unknown')
                confidence = detection.get('confidence', 0.0)
                
                x1, y1 = int(bbox.get('x1', 0)), int(bbox.get('y1', 0))
                x2, y2 = int(bbox.get('x2', 0)), int(bbox.get('y2', 0))
                
                # Draw bounding box
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Add label
                label = f"{vehicle_type} ({confidence:.2f})"
                cv2.putText(annotated_image, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 2. Add Analysis Information Overlay (Lane visualization removed)
            self._add_info_overlay(annotated_image, analysis_results)
            
            return annotated_image
            
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return cv2.imread(image_path) if cv2.imread(image_path) is not None else np.zeros((480, 640, 3), dtype=np.uint8)
    
    def _add_info_overlay(self, image: np.ndarray, results: Dict[str, Any]):
        """Add information overlay to the image"""
        try:
            height, width = image.shape[:2]
            
            # Create semi-transparent overlay
            overlay = image.copy()
            
            # Info panel background
            cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
            
            # Add text information
            y_offset = 30
            line_height = 20
            
            info_lines = [
                f"Vehicles: {results.get('vehicle_detection', {}).get('total_vehicles', 0)}",
                f"Scene: {results.get('scene_analysis', {}).get('scene_type', 'unknown')}",
                f"Weather: {results.get('scene_analysis', {}).get('weather_condition', 'unknown')}",
                f"Density: {results.get('enhanced_traffic_density', {}).get('density_level', 'unknown')}",
                f"Processing: {results.get('performance_metrics', {}).get('processing_time', 0):.2f}s"
            ]
            
            for i, line in enumerate(info_lines):
                y_pos = y_offset + i * line_height
                cv2.putText(image, line, (20, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        except Exception as e:
            logger.error(f"Info overlay error: {e}")
    
    def export_analysis_report(self, analysis_results: Dict[str, Any], 
                             output_path: str, format: str = 'json') -> bool:
        """
        Export comprehensive analysis report
        
        Args:
            analysis_results: Analysis results to export
            output_path: Output file path
            format: Export format ('json', 'csv', 'html')
            
        Returns:
            Success status
        """
        try:
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(analysis_results, f, indent=2, default=str)
            
            elif format.lower() == 'csv':
                import pandas as pd
                
                # Flatten results for CSV
                flattened_data = self._flatten_dict(analysis_results)
                df = pd.DataFrame([flattened_data])
                df.to_csv(output_path, index=False)
            
            elif format.lower() == 'html':
                html_content = self._generate_html_report(analysis_results)
                with open(output_path, 'w') as f:
                    f.write(html_content)
            
            logger.info(f"Analysis report exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Advanced Traffic Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .metric { display: inline-block; margin: 10px; padding: 10px; background-color: #e9e9e9; border-radius: 3px; }
                .recommendations { background-color: #fff3cd; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Advanced Traffic Analysis Report</h1>
                <p>Generated on: {timestamp}</p>
            </div>
            
            <div class="section">
                <h2>Vehicle Detection</h2>
                <div class="metric">Total Vehicles: {total_vehicles}</div>
                <div class="metric">Average Confidence: {avg_confidence:.2f}</div>
            </div>
            
            <div class="section">
                <h2>Scene Analysis</h2>
                <div class="metric">Scene Type: {scene_type}</div>
                <div class="metric">Weather: {weather}</div>
                <div class="metric">Time of Day: {time_of_day}</div>
            </div>
            
            <div class="section">
                <h2>Lane Analysis</h2>
                <div class="metric">Status: Removed per user request</div>
                <div class="metric">Note: Feature no longer available</div>
            </div>
            
            <div class="recommendations">
                <h2>AI Recommendations</h2>
                <ul>
                {recommendations}
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Extract data for template
        vehicle_data = results.get('vehicle_detection', {})
        scene_data = results.get('scene_analysis', {})
        lane_data = results.get('lane_analysis', {})
        ai_data = results.get('ai_insights', {})
        
        recommendations_html = ''.join([
            f"<li>{rec}</li>" for rec in ai_data.get('recommendations', [])
        ])
        
        return html_template.format(
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            total_vehicles=vehicle_data.get('total_vehicles', 0),
            avg_confidence=vehicle_data.get('average_confidence', 0),
            scene_type=scene_data.get('scene_type', 'unknown'),
            weather=scene_data.get('weather_condition', 'unknown'),
            time_of_day=scene_data.get('time_of_day', 'unknown'),
            recommendations=recommendations_html
        )