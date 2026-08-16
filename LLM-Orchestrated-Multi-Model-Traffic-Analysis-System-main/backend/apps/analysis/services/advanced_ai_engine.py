"""
Advanced AI Processing Engine for Comprehensive Traffic Analysis
Implements deep learning models for enhanced traffic understanding
"""
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import time
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class AdvancedAIEngine:
    """
    Advanced AI processing engine using deep learning for comprehensive traffic analysis
    """
    
    def __init__(self, device: str = 'auto'):
        """
        Initialize the advanced AI engine
        
        Args:
            device: Device to use ('cpu', 'cuda', or 'auto')
        """
        self.device = self._setup_device(device)
        self.models = {}
        self.transforms = self._setup_transforms()
        
        # Initialize specialized models
        self._load_scene_classifier()
        self._load_weather_detector()
        self._load_time_classifier()
        self._load_traffic_flow_predictor()
        
        logger.info(f"Advanced AI Engine initialized on device: {self.device}")
    
    def _setup_device(self, device: str) -> str:
        """Setup computation device"""
        if device == 'auto':
            if torch.cuda.is_available():
                return 'cuda'
            else:
                return 'cpu'
        return device
    
    def _setup_transforms(self) -> Dict[str, transforms.Compose]:
        """Setup image transforms for different models"""
        return {
            'scene_classification': transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ]),
            'weather_detection': transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], 
                                   std=[0.5, 0.5, 0.5])
            ]),
            'flow_analysis': transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((512, 512)),
                transforms.ToTensor()
            ])
        }
    
    def _load_scene_classifier(self):
        """Load scene classification model"""
        try:
            # Use a pre-trained ResNet for scene classification
            from torchvision.models import resnet50
            model = resnet50(pretrained=True)
            
            # Modify for traffic scene classification
            num_classes = 8  # highway, urban, intersection, parking, etc.
            model.fc = nn.Linear(model.fc.in_features, num_classes)
            
            model.eval()
            model.to(self.device)
            self.models['scene_classifier'] = model
            
            # Scene class mapping
            self.scene_classes = {
                0: 'highway',
                1: 'urban_street',
                2: 'intersection',
                3: 'parking_lot',
                4: 'residential',
                5: 'commercial',
                6: 'industrial',
                7: 'rural_road'
            }
            
            logger.info("Scene classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load scene classifier: {e}")
            self.models['scene_classifier'] = None
    
    def _load_weather_detector(self):
        """Load weather condition detection model"""
        try:
            # Simple CNN for weather detection
            class WeatherNet(nn.Module):
                def __init__(self, num_classes=6):
                    super(WeatherNet, self).__init__()
                    self.features = nn.Sequential(
                        nn.Conv2d(3, 64, 3, padding=1),
                        nn.ReLU(inplace=True),
                        nn.MaxPool2d(2),
                        nn.Conv2d(64, 128, 3, padding=1),
                        nn.ReLU(inplace=True),
                        nn.MaxPool2d(2),
                        nn.Conv2d(128, 256, 3, padding=1),
                        nn.ReLU(inplace=True),
                        nn.AdaptiveAvgPool2d((7, 7))
                    )
                    self.classifier = nn.Sequential(
                        nn.Linear(256 * 7 * 7, 512),
                        nn.ReLU(inplace=True),
                        nn.Dropout(0.5),
                        nn.Linear(512, num_classes)
                    )
                
                def forward(self, x):
                    x = self.features(x)
                    x = x.view(x.size(0), -1)
                    x = self.classifier(x)
                    return x
            
            model = WeatherNet()
            model.eval()
            model.to(self.device)
            self.models['weather_detector'] = model
            
            # Weather class mapping
            self.weather_classes = {
                0: 'clear',
                1: 'cloudy',
                2: 'rainy',
                3: 'foggy',
                4: 'snowy',
                5: 'night'
            }
            
            logger.info("Weather detector loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load weather detector: {e}")
            self.models['weather_detector'] = None
    
    def _load_time_classifier(self):
        """Load time of day classifier"""
        try:
            # Simple model for time classification based on lighting
            class TimeClassifier(nn.Module):
                def __init__(self):
                    super(TimeClassifier, self).__init__()
                    self.features = nn.Sequential(
                        nn.Conv2d(3, 32, 5),
                        nn.ReLU(),
                        nn.MaxPool2d(2),
                        nn.Conv2d(32, 64, 5),
                        nn.ReLU(),
                        nn.AdaptiveAvgPool2d((1, 1))
                    )
                    self.classifier = nn.Linear(64, 4)  # morning, afternoon, evening, night
                
                def forward(self, x):
                    x = self.features(x)
                    x = x.view(x.size(0), -1)
                    return self.classifier(x)
            
            model = TimeClassifier()
            model.eval()
            model.to(self.device)
            self.models['time_classifier'] = model
            
            # Time class mapping
            self.time_classes = {
                0: 'morning',
                1: 'afternoon', 
                2: 'evening',
                3: 'night'
            }
            
            logger.info("Time classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load time classifier: {e}")
            self.models['time_classifier'] = None
    
    def _load_traffic_flow_predictor(self):
        """Load traffic flow prediction model"""
        try:
            # LSTM-based model for traffic flow prediction
            class TrafficFlowPredictor(nn.Module):
                def __init__(self, input_size=10, hidden_size=64, num_layers=2):
                    super(TrafficFlowPredictor, self).__init__()
                    self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                    self.fc = nn.Linear(hidden_size, 3)  # predict next 3 time steps
                
                def forward(self, x):
                    lstm_out, _ = self.lstm(x)
                    return self.fc(lstm_out[:, -1, :])
            
            model = TrafficFlowPredictor()
            model.eval()
            model.to(self.device)
            self.models['flow_predictor'] = model
            
            logger.info("Traffic flow predictor loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load traffic flow predictor: {e}")
            self.models['flow_predictor'] = None
    
    def analyze_scene_context(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze scene context using AI models
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with scene analysis results
        """
        results = {
            'scene_type': 'unknown',
            'weather_condition': 'unknown',
            'time_of_day': 'unknown',
            'lighting_quality': 'unknown',
            'visibility_score': 0.0,
            'scene_complexity': 'medium'
        }
        
        try:
            # Convert BGR to RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Scene classification
            if self.models['scene_classifier'] is not None:
                scene_result = self._classify_scene(image_rgb)
                results.update(scene_result)
            
            # Weather detection
            if self.models['weather_detector'] is not None:
                weather_result = self._detect_weather(image_rgb)
                results.update(weather_result)
            
            # Time classification
            if self.models['time_classifier'] is not None:
                time_result = self._classify_time(image_rgb)
                results.update(time_result)
            
            # Additional analysis
            results.update(self._analyze_image_quality(image_rgb))
            results.update(self._analyze_scene_complexity(image_rgb))
            
        except Exception as e:
            logger.error(f"Error in scene context analysis: {e}")
        
        return results
    
    def _classify_scene(self, image: np.ndarray) -> Dict[str, Any]:
        """Classify traffic scene type"""
        try:
            # Preprocess image
            input_tensor = self.transforms['scene_classification'](image).unsqueeze(0)
            input_tensor = input_tensor.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.models['scene_classifier'](input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_class].item()
            
            scene_type = self.scene_classes.get(predicted_class, 'unknown')
            
            return {
                'scene_type': scene_type,
                'scene_confidence': confidence,
                'scene_probabilities': {
                    self.scene_classes[i]: probabilities[0][i].item() 
                    for i in range(len(self.scene_classes))
                }
            }
        except Exception as e:
            logger.error(f"Scene classification error: {e}")
            return {'scene_type': 'unknown', 'scene_confidence': 0.0}
    
    def _detect_weather(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect weather conditions"""
        try:
            # Preprocess image
            input_tensor = self.transforms['weather_detection'](image).unsqueeze(0)
            input_tensor = input_tensor.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.models['weather_detector'](input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_class].item()
            
            weather_condition = self.weather_classes.get(predicted_class, 'unknown')
            
            return {
                'weather_condition': weather_condition,
                'weather_confidence': confidence,
                'weather_probabilities': {
                    self.weather_classes[i]: probabilities[0][i].item() 
                    for i in range(len(self.weather_classes))
                }
            }
        except Exception as e:
            logger.error(f"Weather detection error: {e}")
            return {'weather_condition': 'unknown', 'weather_confidence': 0.0}
    
    def _classify_time(self, image: np.ndarray) -> Dict[str, Any]:
        """Classify time of day"""
        try:
            # Analyze brightness and color temperature
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            mean_brightness = np.mean(gray)
            
            # Simple heuristic-based classification
            if mean_brightness < 50:
                time_of_day = 'night'
                confidence = 0.9
            elif mean_brightness < 100:
                time_of_day = 'evening'
                confidence = 0.7
            elif mean_brightness < 180:
                time_of_day = 'morning'
                confidence = 0.6
            else:
                time_of_day = 'afternoon'
                confidence = 0.8
            
            return {
                'time_of_day': time_of_day,
                'time_confidence': confidence,
                'brightness_level': mean_brightness
            }
        except Exception as e:
            logger.error(f"Time classification error: {e}")
            return {'time_of_day': 'unknown', 'time_confidence': 0.0}
    
    def _analyze_image_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image quality metrics"""
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Calculate sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate contrast (standard deviation)
            contrast = np.std(gray)
            
            # Calculate brightness
            brightness = np.mean(gray)
            
            # Determine quality levels
            if laplacian_var > 500:
                sharpness_quality = 'high'
            elif laplacian_var > 100:
                sharpness_quality = 'medium'
            else:
                sharpness_quality = 'low'
            
            if contrast > 50:
                contrast_quality = 'high'
            elif contrast > 25:
                contrast_quality = 'medium'
            else:
                contrast_quality = 'low'
            
            # Overall visibility score
            visibility_score = min(1.0, (laplacian_var / 1000 + contrast / 100) / 2)
            
            return {
                'lighting_quality': sharpness_quality,
                'contrast_quality': contrast_quality,
                'visibility_score': visibility_score,
                'brightness_level': brightness,
                'sharpness_score': laplacian_var,
                'contrast_score': contrast
            }
        except Exception as e:
            logger.error(f"Image quality analysis error: {e}")
            return {
                'lighting_quality': 'unknown',
                'visibility_score': 0.0
            }
    
    def _analyze_scene_complexity(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze scene complexity"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Edge detection for complexity
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Color diversity
            hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            color_diversity = np.count_nonzero(hist) / hist.size
            
            # Determine complexity
            complexity_score = (edge_density + color_diversity) / 2
            
            if complexity_score > 0.3:
                complexity = 'high'
            elif complexity_score > 0.15:
                complexity = 'medium'
            else:
                complexity = 'low'
            
            return {
                'scene_complexity': complexity,
                'complexity_score': complexity_score,
                'edge_density': edge_density,
                'color_diversity': color_diversity
            }
        except Exception as e:
            logger.error(f"Scene complexity analysis error: {e}")
            return {'scene_complexity': 'medium'}
    
    def predict_traffic_flow(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict future traffic flow based on historical data
        
        Args:
            historical_data: List of historical traffic measurements
            
        Returns:
            Dictionary with flow predictions
        """
        try:
            if len(historical_data) < 5:
                return {
                    'prediction': 'insufficient_data',
                    'confidence': 0.0,
                    'trend': 'unknown'
                }
            
            # Extract features from historical data
            vehicle_counts = [data.get('total_vehicles', 0) for data in historical_data[-10:]]
            density_scores = [data.get('density_score', 0) for data in historical_data[-10:]]
            
            # Simple trend analysis
            if len(vehicle_counts) >= 3:
                recent_trend = np.mean(vehicle_counts[-3:]) - np.mean(vehicle_counts[-6:-3])
                
                if recent_trend > 2:
                    trend = 'increasing'
                    prediction = 'traffic_buildup'
                elif recent_trend < -2:
                    trend = 'decreasing'
                    prediction = 'traffic_clearing'
                else:
                    trend = 'stable'
                    prediction = 'steady_flow'
                
                confidence = min(0.9, abs(recent_trend) / 10)
            else:
                trend = 'unknown'
                prediction = 'insufficient_data'
                confidence = 0.0
            
            return {
                'prediction': prediction,
                'trend': trend,
                'confidence': confidence,
                'predicted_change': recent_trend if 'recent_trend' in locals() else 0,
                'recommendation': self._get_flow_recommendation(prediction, trend)
            }
        except Exception as e:
            logger.error(f"Traffic flow prediction error: {e}")
            return {
                'prediction': 'error',
                'confidence': 0.0,
                'trend': 'unknown'
            }
    
    def _get_flow_recommendation(self, prediction: str, trend: str) -> str:
        """Get traffic flow recommendation"""
        recommendations = {
            'traffic_buildup': 'Consider alternative routes or delay travel if possible',
            'traffic_clearing': 'Good time to travel, conditions are improving',
            'steady_flow': 'Normal traffic conditions, proceed as planned',
            'insufficient_data': 'Monitor conditions and gather more data'
        }
        return recommendations.get(prediction, 'Monitor traffic conditions')
    
    def generate_ai_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered insights from analysis results
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Dictionary with AI insights
        """
        insights = {
            'key_findings': [],
            'recommendations': [],
            'risk_assessment': 'low',
            'optimization_suggestions': [],
            'confidence_score': 0.0
        }
        
        try:
            # Extract key metrics
            total_vehicles = analysis_results.get('total_vehicles', 0)
            scene_type = analysis_results.get('scene_type', 'unknown')
            weather = analysis_results.get('weather_condition', 'unknown')
            time_of_day = analysis_results.get('time_of_day', 'unknown')
            density_level = analysis_results.get('density_level', 'unknown')
            
            # Generate key findings
            if total_vehicles == 0:
                insights['key_findings'].append("No vehicles detected - road appears empty")
                insights['risk_assessment'] = 'low'
            elif total_vehicles > 20:
                insights['key_findings'].append(f"High vehicle density detected ({total_vehicles} vehicles)")
                insights['risk_assessment'] = 'high'
            else:
                insights['key_findings'].append(f"Moderate traffic with {total_vehicles} vehicles")
                insights['risk_assessment'] = 'medium'
            
            # Scene-specific insights
            if scene_type == 'intersection':
                insights['key_findings'].append("Intersection detected - monitor for traffic conflicts")
                insights['recommendations'].append("Implement traffic signal optimization")
            elif scene_type == 'highway':
                insights['key_findings'].append("Highway traffic - monitor for speed variations")
                insights['recommendations'].append("Consider dynamic speed limits")
            
            # Weather-based recommendations
            if weather in ['rainy', 'foggy', 'snowy']:
                insights['recommendations'].append("Adverse weather conditions - reduce speed limits")
                insights['risk_assessment'] = 'high'
            
            # Time-based insights
            if time_of_day in ['morning', 'evening']:
                insights['key_findings'].append("Peak hour conditions detected")
                insights['recommendations'].append("Activate rush hour traffic management")
            
            # Optimization suggestions
            if density_level == 'High':
                insights['optimization_suggestions'].extend([
                    "Deploy additional traffic controllers",
                    "Activate alternate route signage",
                    "Implement adaptive signal timing"
                ])
            
            # Calculate overall confidence
            confidence_factors = []
            if 'scene_confidence' in analysis_results:
                confidence_factors.append(analysis_results['scene_confidence'])
            if 'weather_confidence' in analysis_results:
                confidence_factors.append(analysis_results['weather_confidence'])
            
            insights['confidence_score'] = np.mean(confidence_factors) if confidence_factors else 0.7
            
        except Exception as e:
            logger.error(f"AI insights generation error: {e}")
        
        return insights