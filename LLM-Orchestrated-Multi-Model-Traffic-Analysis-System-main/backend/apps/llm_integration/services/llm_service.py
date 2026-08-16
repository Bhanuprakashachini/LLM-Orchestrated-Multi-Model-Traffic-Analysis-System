"""
LLM Integration Service for Traffic Analysis Intelligence - MongoDB compatible
"""
import json
from typing import Dict, Any, List, Optional
from django.conf import settings
from pymongo import MongoClient
from datetime import datetime
import logging

# Initialize logger first
logger = logging.getLogger(__name__)

# Optional imports for different LLM providers
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI not available")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available - using Groq only")

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]
llm_providers = db.llm_providers
conversation_sessions = db.conversation_sessions
llm_messages = db.llm_messages
traffic_insights = db.traffic_insights
scene_descriptions = db.scene_descriptions

class LLMService:
    """
    Service for integrating Large Language Models with traffic analysis
    Supports multiple free LLM providers: Ollama, Groq, Gemini, Hugging Face
    """
    
    def __init__(self):
        self.default_provider = self._get_default_provider()
        self.provider_type = getattr(settings, 'LLM_PROVIDER', 'ollama')  # Default to Ollama
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the selected LLM provider - optimized for Groq with gpt-oss-20b"""
        try:
            if self.provider_type == 'groq' and GROQ_AVAILABLE:
                groq_api_key = getattr(settings, 'GROQ_API_KEY', '')
                if groq_api_key:
                    self.groq_client = Groq(api_key=groq_api_key)
                    self.groq_model = getattr(settings, 'GROQ_MODEL', 'gpt-oss-20b')
                    self.groq_backup_model = getattr(settings, 'GROQ_BACKUP_MODEL', 'llama-3.1-70b-versatile')
                    self.groq_fallback_model = getattr(settings, 'GROQ_FALLBACK_MODEL', 'llama-3.1-8b-instant')
                    self.groq_max_tokens = getattr(settings, 'GROQ_MAX_TOKENS', 1000)
                    self.groq_temperature = getattr(settings, 'GROQ_TEMPERATURE', 0.7)
                    self.groq_top_p = getattr(settings, 'GROQ_TOP_P', 0.9)
                    logger.info(f"Initialized Groq provider with primary model: {self.groq_model}")
                else:
                    logger.error("Groq API key not found in settings")
                    self.provider_type = 'fallback'
                    
            elif self.provider_type == 'ollama':
                self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
                self.ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:3b')
                logger.info(f"Initialized Ollama provider with model: {self.ollama_model}")
                
            elif self.provider_type == 'gemini' and GEMINI_AVAILABLE:
                gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
                if gemini_api_key:
                    genai.configure(api_key=gemini_api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("Initialized Gemini provider")
                
            elif self.provider_type == 'huggingface' and TRANSFORMERS_AVAILABLE:
                model_name = getattr(settings, 'HF_MODEL', 'microsoft/DialoGPT-medium')
                self.hf_generator = pipeline("text-generation", model=model_name)
                logger.info(f"Initialized Hugging Face provider with model: {model_name}")
                
            elif self.provider_type == 'openai' and OPENAI_AVAILABLE:
                openai.api_key = getattr(settings, 'OPENAI_API_KEY', '')
                logger.info("Initialized OpenAI provider")
            else:
                logger.warning(f"Provider {self.provider_type} not available, using fallback")
                self.provider_type = 'fallback'
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider {self.provider_type}: {e}")
            self.provider_type = 'fallback'
    
    def generate_feature_specific_insights(self, analysis_data: Dict[str, Any], feature_type: str, user_id: str) -> Dict[str, Any]:
        """
        Generate specific insights for individual features based on analysis data
        """
        try:
            # Extract key metrics
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            vehicle_count = vehicle_detection.get('total_vehicles', 0)
            vehicle_counts = vehicle_detection.get('vehicle_counts', {})
            density_data = analysis_data.get('traffic_density', {})
            model_comparison = analysis_data.get('model_comparison', [])
            
            # Calculate vehicle composition
            cars = vehicle_counts.get('cars', 0)
            large_vehicles = vehicle_counts.get('large_vehicles', 0) + vehicle_counts.get('trucks', 0) + vehicle_counts.get('buses', 0)
            two_wheelers = vehicle_counts.get('2_wheelers', 0) + vehicle_counts.get('motorcycles', 0) + vehicle_counts.get('bicycles', 0)
            total_detected = cars + large_vehicles + two_wheelers
            
            # Generate feature-specific prompts
            if feature_type == 'vehicle-detection':
                prompt = f"""As a vehicle detection specialist, analyze this specific detection result:

DETECTION RESULTS:
- Total Vehicles Detected: {vehicle_count}
- Cars: {cars} ({(cars/max(total_detected,1)*100):.1f}%)
- Large Vehicles: {large_vehicles} ({(large_vehicles/max(total_detected,1)*100):.1f}%)
- Two-Wheelers: {two_wheelers} ({(two_wheelers/max(total_detected,1)*100):.1f}%)

Provide a focused analysis covering:
1. Detection accuracy assessment for this specific count
2. Vehicle type distribution analysis
3. Detection challenges in this scene
4. Confidence in the detection results
5. Recommendations for improving detection

Keep response concise (3-4 sentences) and specific to these exact numbers."""

            elif feature_type == 'traffic-density':
                congestion_index = density_data.get('congestion_index', 0)
                density_level = density_data.get('density_level', 'Unknown')
                
                prompt = f"""As a traffic flow analyst, evaluate this density situation:

DENSITY METRICS:
- Vehicle Count: {vehicle_count} vehicles
- Density Level: {density_level}
- Congestion Index: {congestion_index:.2f}
- Flow Status: {'Congested' if congestion_index > 0.7 else 'Moderate' if congestion_index > 0.4 else 'Free Flow'}

Analyze:
1. Current traffic density implications
2. Flow characteristics with {vehicle_count} vehicles
3. Congestion risk assessment
4. Traffic management recommendations
5. Expected flow patterns

Keep response focused on density and flow (3-4 sentences)."""

            elif feature_type == 'model-comparison':
                if model_comparison and len(model_comparison) > 0:
                    best_model = model_comparison[0]
                    model_name = best_model.get('model_name', 'Unknown')
                    accuracy = best_model.get('estimated_accuracy', 0)
                    
                    # Ensure accuracy is a number for formatting
                    try:
                        if isinstance(accuracy, str):
                            # Remove % sign if present and convert to float
                            accuracy = float(accuracy.replace('%', '')) / 100 if '%' in accuracy else float(accuracy)
                        accuracy = float(accuracy)
                    except (ValueError, TypeError):
                        accuracy = 0.0
                    
                    prompt = f"""As an AI model performance analyst, evaluate this comparison:

MODEL PERFORMANCE:
- Models Compared: {len(model_comparison)}
- Best Model: {model_name}
- Accuracy: {accuracy:.1%}
- Vehicles Detected: {vehicle_count}
- Detection Quality: {'Excellent' if accuracy > 0.9 else 'Good' if accuracy > 0.8 else 'Fair'}

Analyze:
1. Model selection rationale for this scene
2. Performance comparison insights
3. Accuracy assessment for this vehicle count
4. Model suitability for this traffic type
5. Confidence in model choice

Keep response focused on model performance (3-4 sentences)."""
                else:
                    prompt = f"Model comparison data not available. Analysis performed with single model detecting {vehicle_count} vehicles with good accuracy."

            elif feature_type == 'visualization':
                prompt = f"""As a data visualization expert, analyze this traffic visualization:

VISUALIZATION DATA:
- Total Vehicles: {vehicle_count}
- Vehicle Types: {len([v for v in vehicle_counts.values() if v > 0])} categories
- Data Distribution: Cars {cars}, Large Vehicles {large_vehicles}, Two-Wheelers {two_wheelers}
- Chart Complexity: {'High' if total_detected > 20 else 'Medium' if total_detected > 10 else 'Simple'}

Analyze:
1. Data visualization effectiveness for this dataset
2. Chart readability with {vehicle_count} vehicles
3. Visual pattern insights
4. Recommended visualization improvements
5. Data presentation clarity

Keep response focused on visualization aspects (3-4 sentences)."""

            elif feature_type == 'history-reports':
                prompt = f"""As a traffic reporting analyst, evaluate this analysis for reporting:

REPORT DATA:
- Analysis Scope: {vehicle_count} vehicles detected
- Data Quality: {'Comprehensive' if total_detected > 15 else 'Standard' if total_detected > 5 else 'Basic'}
- Report Categories: {len([v for v in vehicle_counts.values() if v > 0])} vehicle types
- Analysis Depth: {'Detailed' if vehicle_count > 20 else 'Standard'}

Analyze:
1. Report completeness for this dataset
2. Historical comparison value
3. Data export recommendations
4. Report format suitability
5. Long-term trend analysis potential

Keep response focused on reporting aspects (3-4 sentences)."""

            else:
                # Default general insight
                prompt = f"""Analyze this traffic situation with {vehicle_count} vehicles: {cars} cars, {large_vehicles} large vehicles, {two_wheelers} two-wheelers. Provide specific insights about this exact composition and what it indicates about traffic patterns. Keep response concise (3-4 sentences)."""

            # Get LLM response
            response = self._call_llm(prompt, user_id, f'feature_insight_{feature_type}')
            
            # Check if response is a fallback (contains timestamp pattern)
            is_fallback_response = 'Service Status:' in response or 'fallback response generated at' in response
            model_used = 'fallback' if is_fallback_response else (self.groq_model if self.provider_type == 'groq' else self.provider_type)
            
            # Store feature-specific insight
            insight_data = {
                'user_id': user_id,
                'insight_type': f'feature_specific_{feature_type}',
                'feature_type': feature_type,
                'content': response,
                'analysis_data': analysis_data,
                'unique_signature': f"{feature_type}_{vehicle_count}_{cars}_{large_vehicles}_{two_wheelers}",
                'model_used': model_used,
                'created_at': datetime.utcnow(),
                'is_fallback': is_fallback_response
            }
            traffic_insights.insert_one(insight_data)
            
            return {
                'success': True,
                'insight': response,
                'feature_type': feature_type,
                'model_used': model_used,
                'is_fallback': is_fallback_response,
                'analysis_summary': {
                    'vehicle_count': vehicle_count,
                    'feature_focus': feature_type,
                    'data_quality': 'high' if total_detected > 10 else 'medium'
                }
            }
            
        except Exception as e:
            logger.error(f"Feature-specific insight generation failed: {e}")
            
            # Use fallback response instead of error
            fallback_response = self._generate_fallback_response(f'feature_insight_{feature_type}')
            
            # Store fallback insight
            insight_data = {
                'user_id': user_id,
                'insight_type': f'feature_specific_{feature_type}',
                'feature_type': feature_type,
                'content': fallback_response,
                'analysis_data': analysis_data,
                'unique_signature': f"{feature_type}_{vehicle_count}_{cars}_{large_vehicles}_{two_wheelers}",
                'model_used': 'fallback',
                'created_at': datetime.utcnow(),
                'is_fallback': True
            }
            
            try:
                traffic_insights.insert_one(insight_data)
            except Exception as db_error:
                logger.error(f"Failed to store fallback insight: {db_error}")
            
            return {
                'success': True,  # Changed to True since we have fallback content
                'insight': fallback_response,
                'feature_type': feature_type,
                'model_used': 'fallback',
                'is_fallback': True,
                'analysis_summary': {
                    'vehicle_count': vehicle_count,
                    'feature_focus': feature_type,
                    'data_quality': 'high' if total_detected > 10 else 'medium'
                }
            }

    def analyze_traffic_conditions(self, analysis_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate intelligent insights about traffic conditions using Groq gpt-oss-20b model
        """
        try:
            # Extract key metrics
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            vehicle_count = vehicle_detection.get('total_vehicles', 0)
            vehicle_counts = vehicle_detection.get('vehicle_counts', {})
            scene_type = analysis_data.get('scene_classification', {}).get('scene_type', 'traffic scene')
            density_data = analysis_data.get('traffic_density', {})
            density_level = density_data.get('density_level', 'Unknown')
            congestion_index = density_data.get('congestion_index', 0)
            best_model = analysis_data.get('best_model', 'Unknown')
            detection_quality = analysis_data.get('detection_quality', 'Unknown')
            model_comparison = analysis_data.get('model_comparison', [])
            
            # Calculate traffic density level based on vehicle count
            if vehicle_count == 0:
                calculated_density = "No Traffic"
                congestion_level = "Free Flow"
                traffic_status = "Clear"
                urgency_level = "None"
                risk_level = "Minimal"
            elif vehicle_count <= 5:
                calculated_density = "Light Traffic"
                congestion_level = "Free Flow"
                traffic_status = "Smooth"
                urgency_level = "Low"
                risk_level = "Low"
            elif vehicle_count <= 15:
                calculated_density = "Moderate Traffic"
                congestion_level = "Stable Flow"
                traffic_status = "Normal"
                urgency_level = "Medium"
                risk_level = "Moderate"
            elif vehicle_count <= 25:
                calculated_density = "Heavy Traffic"
                congestion_level = "Congested"
                traffic_status = "Busy"
                urgency_level = "High"
                risk_level = "High"
            else:
                calculated_density = "Very Heavy Traffic"
                congestion_level = "Severely Congested"
                traffic_status = "Gridlock Risk"
                urgency_level = "Critical"
                risk_level = "Very High"
            
            # Calculate congestion index
            calculated_congestion = min(vehicle_count / 30.0, 1.0)  # Scale to 0-1
            
            # Analyze vehicle composition with specific insights
            cars = vehicle_counts.get('cars', 0)
            large_vehicles = vehicle_counts.get('large_vehicles', 0) + vehicle_counts.get('trucks', 0) + vehicle_counts.get('buses', 0)
            two_wheelers = vehicle_counts.get('2_wheelers', 0) + vehicle_counts.get('motorcycles', 0) + vehicle_counts.get('bicycles', 0)
            
            # Generate specific vehicle composition insights
            total_detected = cars + large_vehicles + two_wheelers
            if total_detected > 0:
                car_percentage = (cars / total_detected) * 100
                large_percentage = (large_vehicles / total_detected) * 100
                two_wheeler_percentage = (two_wheelers / total_detected) * 100
            else:
                car_percentage = large_percentage = two_wheeler_percentage = 0
            
            # Determine dominant vehicle type and specific characteristics
            if cars > large_vehicles and cars > two_wheelers:
                dominant_vehicle = "passenger cars"
                traffic_type = "typical urban commuter traffic"
                composition_insight = f"Passenger car dominated ({car_percentage:.1f}%) indicating typical commuter patterns"
            elif large_vehicles > cars and large_vehicles > two_wheelers:
                dominant_vehicle = "commercial vehicles"
                traffic_type = "freight/commercial corridor"
                composition_insight = f"Commercial vehicle heavy ({large_percentage:.1f}%) suggesting freight route or industrial area"
            elif two_wheelers > cars and two_wheelers > large_vehicles:
                dominant_vehicle = "two-wheelers"
                traffic_type = "mixed urban traffic with high motorcycle usage"
                composition_insight = f"Two-wheeler dominated ({two_wheeler_percentage:.1f}%) typical of dense urban areas or developing regions"
            else:
                dominant_vehicle = "mixed vehicles"
                traffic_type = "balanced traffic composition"
                composition_insight = f"Balanced mix: {car_percentage:.1f}% cars, {large_percentage:.1f}% large vehicles, {two_wheeler_percentage:.1f}% two-wheelers"
            
            # Generate time-based insights (simulate different times of day)
            import datetime
            current_hour = datetime.datetime.now().hour
            if 6 <= current_hour <= 9:
                time_context = "morning rush hour"
                time_insight = "Peak morning commute period - expect continued high volume"
            elif 17 <= current_hour <= 19:
                time_context = "evening rush hour"
                time_insight = "Peak evening commute period - monitor for extended congestion"
            elif 10 <= current_hour <= 16:
                time_context = "midday period"
                time_insight = "Off-peak hours - current levels may indicate incidents or events"
            elif 20 <= current_hour <= 23:
                time_context = "evening hours"
                time_insight = "Evening period - monitor for recreational or event-related traffic"
            else:
                time_context = "overnight hours"
                time_insight = "Off-peak overnight period - unusual activity may indicate incidents"
            
            # Generate specific safety concerns based on actual data
            safety_concerns = []
            if large_vehicles > 3:
                safety_concerns.append(f"High commercial vehicle presence ({large_vehicles} detected) requires enhanced safety monitoring")
            if two_wheelers > 5:
                safety_concerns.append(f"Significant two-wheeler traffic ({two_wheelers} detected) increases vulnerability risk")
            if vehicle_count > 20:
                safety_concerns.append("Dense traffic conditions increase rear-end collision risk")
            if calculated_congestion > 0.8:
                safety_concerns.append("High congestion levels may lead to aggressive driving behaviors")
            
            # Generate model performance summary with specific details
            model_performance_text = ""
            if model_comparison and len(model_comparison) > 0:
                best_model_info = model_comparison[0]
                model_name = best_model_info.get('model_name', best_model)
                accuracy = best_model_info.get('estimated_accuracy', 'high')
                processing_time = best_model_info.get('processing_time', 'fast')
                confidence = best_model_info.get('avg_confidence', 'high')
                
                model_performance_text = f"Analysis performed using {len(model_comparison)} AI models. {model_name} selected as optimal with {accuracy} accuracy, processing in {processing_time}. This model excelled in detecting {dominant_vehicle} in {traffic_type} scenarios."
            else:
                model_performance_text = f"Analysis completed using {best_model} with {detection_quality} detection quality, optimized for {traffic_type} conditions."
            
            # Create unique, data-specific prompt
            prompt = f"""You are a senior traffic analysis expert providing a detailed report for this specific traffic situation. Generate a comprehensive, unique analysis based on these EXACT conditions:

SPECIFIC TRAFFIC SITUATION ANALYSIS:
- Exact Location: {scene_type}
- Precise Vehicle Count: {vehicle_count} vehicles detected
- Specific Composition: {cars} cars, {large_vehicles} large vehicles, {two_wheelers} two-wheelers
- Traffic Classification: {calculated_density} ({traffic_status})
- Flow Condition: {congestion_level}
- Congestion Level: {calculated_congestion:.1%} congestion index
- Time Context: {time_context}
- Dominant Pattern: {composition_insight}
- Risk Assessment: {risk_level} risk level
- Urgency: {urgency_level} priority

UNIQUE CHARACTERISTICS OF THIS SCENE:
- Vehicle Mix: {composition_insight}
- Time Factor: {time_insight}
- Safety Profile: {'; '.join(safety_concerns) if safety_concerns else 'Standard safety conditions observed'}

AI DETECTION PERFORMANCE:
{model_performance_text}

Generate a UNIQUE, SPECIFIC analysis report with these sections (make each section specific to the actual data above):

## 🚦 CURRENT TRAFFIC SITUATION
Describe this EXACT traffic scene with {vehicle_count} vehicles. Be specific about what makes this situation unique - the exact vehicle mix, density level, and flow characteristics. Reference the specific numbers and percentages.

## 📊 DETAILED BREAKDOWN  
Analyze the specific composition of {cars} cars, {large_vehicles} large vehicles, and {two_wheelers} two-wheelers. Explain what this exact mix indicates about the location type, time of day, and traffic patterns. Calculate and discuss the specific percentages and their implications.

## ⚠️ POTENTIAL ISSUES & RISKS
Based on the EXACT vehicle count of {vehicle_count} and composition, identify specific risks. Address the {risk_level} risk level and {urgency_level} urgency. Be specific about why these exact numbers create particular concerns.

## 💡 RECOMMENDATIONS
Provide specific recommendations for managing exactly {vehicle_count} vehicles with this exact composition in this {scene_type}. Address the {urgency_level} urgency level with appropriate response timing.

## 🎯 KEY INSIGHTS
Summarize the most important findings about this specific traffic situation. What makes this {vehicle_count}-vehicle scene unique? How does the {car_percentage:.1f}% cars, {large_percentage:.1f}% large vehicles, {two_wheeler_percentage:.1f}% two-wheelers mix affect management strategies?

CRITICAL: Make every sentence specific to the actual data provided. Use the exact numbers, percentages, and classifications. Avoid generic statements - everything should be tailored to this unique traffic situation with {vehicle_count} vehicles in this specific composition."""
            
            # Get LLM response
            response = self._call_llm(prompt, user_id, 'traffic_analysis')
            
            # Store insight in MongoDB with unique identifier
            insight_data = {
                'user_id': user_id,
                'insight_type': 'traffic_condition_analysis',
                'content': response,
                'analysis_data': analysis_data,
                'unique_signature': f"{vehicle_count}_{cars}_{large_vehicles}_{two_wheelers}_{int(calculated_congestion*100)}",
                'model_used': self.groq_model if self.provider_type == 'groq' else self.provider_type,
                'created_at': datetime.utcnow()
            }
            traffic_insights.insert_one(insight_data)
            
            return {
                'success': True,
                'insight': response,
                'analysis_summary': {
                    'vehicle_count': vehicle_count,
                    'vehicle_breakdown': {
                        'cars': cars,
                        'cars_percentage': car_percentage,
                        'large_vehicles': large_vehicles,
                        'large_vehicles_percentage': large_percentage,
                        'two_wheelers': two_wheelers,
                        'two_wheelers_percentage': two_wheeler_percentage
                    },
                    'scene_type': scene_type,
                    'density_level': calculated_density,
                    'congestion_index': calculated_congestion,
                    'traffic_status': traffic_status,
                    'dominant_vehicle_type': dominant_vehicle,
                    'traffic_classification': traffic_type,
                    'urgency_level': urgency_level,
                    'risk_level': risk_level,
                    'time_context': time_context,
                    'composition_insight': composition_insight,
                    'safety_concerns': safety_concerns
                },
                'model_used': self.groq_model if self.provider_type == 'groq' else self.provider_type
            }
            
        except Exception as e:
            logger.error(f"Error analyzing traffic conditions: {e}")
            return {
                'success': False,
                'error': str(e),
                'insight': 'Unable to generate traffic analysis at this time.',
                'model_used': self.provider_type
            }
    
    def compare_model_performance(self, comparison_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate insights about model performance comparison using Groq gpt-oss-20b
        """
        try:
            # Extract comparison metrics
            models = comparison_data.get('models', [])
            best_model = comparison_data.get('best_model', 'Unknown')
            performance_metrics = comparison_data.get('performance_metrics', {})
            
            # Analyze specific model performance differences
            model_analysis = []
            performance_gaps = []
            speed_analysis = []
            accuracy_analysis = []
            
            for i, model in enumerate(models):
                model_name = model.get('name', model.get('model_name', 'Unknown'))
                accuracy = model.get('accuracy', model.get('estimated_accuracy', '0%'))
                speed = model.get('processing_time', model.get('speed', 0))
                vehicle_count = model.get('vehicle_count', model.get('total_vehicles', 0))
                confidence = model.get('avg_confidence', '0%') if 'avg_confidence' in model else '0%'  # Keep for backward compatibility but don't use
                grade = model.get('grade', 'N/A')
                f1_score = model.get('f1_score', 'N/A')
                
                rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                
                # Extract numeric values for analysis
                try:
                    accuracy_num = float(accuracy.replace('%', '')) if isinstance(accuracy, str) else float(accuracy) * 100
                    confidence_num = float(confidence.replace('%', '')) if isinstance(confidence, str) else float(confidence) * 100
                    speed_num = float(str(speed).replace('s', '')) if isinstance(speed, str) else float(speed)
                except:
                    accuracy_num = confidence_num = speed_num = 0
                
                model_analysis.append({
                    'rank': i + 1,
                    'name': model_name,
                    'emoji': rank_emoji,
                    'vehicles': vehicle_count,
                    'accuracy': accuracy,
                    'accuracy_num': accuracy_num,
                    'confidence': confidence,
                    'confidence_num': confidence_num,
                    'speed': speed,
                    'speed_num': speed_num,
                    'grade': grade,
                    'f1_score': f1_score
                })
            
            # Calculate performance gaps and insights
            if len(model_analysis) > 1:
                best = model_analysis[0]
                worst = model_analysis[-1]
                
                accuracy_gap = best['accuracy_num'] - worst['accuracy_num']
                speed_gap = worst['speed_num'] - best['speed_num']  # Positive if best is faster
                vehicle_gap = best['vehicles'] - worst['vehicles']
                
                performance_gaps.append(f"Accuracy range: {accuracy_gap:.1f}% difference between best and worst")
                if speed_gap > 0:
                    performance_gaps.append(f"Speed advantage: {best['name']} is {speed_gap:.2f}s faster than {worst['name']}")
                if vehicle_gap != 0:
                    performance_gaps.append(f"Detection difference: {abs(vehicle_gap)} vehicles between top and bottom performers")
            
            # Analyze speed vs accuracy trade-offs
            fastest_model = min(model_analysis, key=lambda x: x['speed_num']) if model_analysis else None
            most_accurate = max(model_analysis, key=lambda x: x['accuracy_num']) if model_analysis else None
            
            if fastest_model and most_accurate and fastest_model['name'] != most_accurate['name']:
                speed_analysis.append(f"{fastest_model['name']} is fastest ({fastest_model['speed']}) but {most_accurate['name']} is most accurate ({most_accurate['accuracy']})")
            
            # Create detailed model analysis prompt with specific data
            model_details = []
            for model in model_analysis:
                model_details.append(f"{model['emoji']} {model['name']}: Detected {model['vehicles']} vehicles with {model['accuracy']} accuracy, processed in {model['speed']} (Grade: {model['grade']})")
            
            # Determine why the best model won with specific reasons
            if model_analysis:
                best_model_data = model_analysis[0]
                best_model_name = best_model_data['name']
                best_accuracy = best_model_data['accuracy']
                best_speed = best_model_data['speed']
                best_vehicles = best_model_data['vehicles']
                best_confidence = best_model_data.get('confidence', '0%')  # Keep for backward compatibility
                best_grade = best_model_data['grade']
                
                # Generate specific winning factors
                winning_factors = []
                if best_model_data['accuracy_num'] >= 90:
                    winning_factors.append(f"exceptional accuracy of {best_accuracy}")
                if best_grade in ['A+', 'A']:
                    winning_factors.append(f"top-tier grade of {best_grade}")
                if best_model_data['speed_num'] < 3:
                    winning_factors.append(f"fast processing time of {best_speed}")
                
                winning_summary = ", ".join(winning_factors) if winning_factors else "balanced performance across all metrics"
            else:
                best_model_name = best_model
                winning_summary = "comprehensive analysis performance"
            
            # Generate unique timestamp-based insights
            import datetime
            analysis_time = datetime.datetime.now()
            time_signature = f"{analysis_time.hour}{analysis_time.minute}{len(models)}{sum(m['vehicles'] for m in model_analysis)}"
            
            prompt = f"""You are an AI performance analyst providing a detailed comparison report for this SPECIFIC model evaluation with {len(models)} models tested. Generate a unique analysis based on these EXACT results:

SPECIFIC MODEL PERFORMANCE RESULTS:
Total Models Tested: {len(models)}
Analysis Timestamp: {analysis_time.strftime('%Y-%m-%d %H:%M:%S')}
Unique Analysis ID: {time_signature}

DETAILED MODEL RANKINGS:
{chr(10).join(model_details)}

WINNING MODEL ANALYSIS:
🏆 Champion: {best_model_name}
🎯 Key Strengths: {winning_summary}
📊 Performance Metrics: {best_vehicles} vehicles, {best_accuracy} accuracy, {best_confidence} confidence, {best_speed} processing

PERFORMANCE GAPS IDENTIFIED:
{chr(10).join(performance_gaps) if performance_gaps else 'Consistent performance across all models'}

SPEED VS ACCURACY ANALYSIS:
{chr(10).join(speed_analysis) if speed_analysis else 'Optimal balance achieved by winning model'}

Generate a UNIQUE, SPECIFIC analysis report with these sections (reference the exact data above):

## 🏆 BEST PERFORMING MODEL ANALYSIS
Explain why {best_model_name} won this specific comparison with {len(models)} models. Detail the exact performance metrics: {best_vehicles} vehicles detected, {best_accuracy} accuracy, processed in {best_speed}. What made this combination superior?

## 📊 DETAILED PERFORMANCE COMPARISON
Compare all {len(models)} models tested, highlighting specific differences:
- Detection accuracy variations: {performance_gaps[0] if performance_gaps else 'Consistent accuracy across models'}
- Processing speed differences: Reference exact timing differences
- Confidence level comparisons: Use actual confidence percentages
- Vehicle count consistency: Analyze detection reliability

## ⚖️ TRADE-OFFS ANALYSIS
Analyze the specific trade-offs in this {len(models)}-model comparison:
- Speed vs Accuracy: {speed_analysis[0] if speed_analysis else 'Optimal balance achieved'}
- Resource usage vs Performance: Based on actual processing times
- Consistency vs Peak performance: Reference actual detection variations

## 🎯 PRACTICAL RECOMMENDATIONS
Based on these EXACT results with {len(models)} models, provide specific recommendations:
- When to use {best_model_name} (the winner): Optimal scenarios
- Alternative model choices: When other models might be preferred
- System configuration: Based on actual performance data
- Performance optimization: Specific to these results

## 💡 KEY INSIGHTS FOR THIS ANALYSIS
Summarize the most important findings from this specific {len(models)}-model comparison:
- What makes {best_model_name} the clear winner with {winning_summary}
- Unique performance characteristics observed
- Practical implications for traffic analysis operations
- Recommendations based on these exact results

CRITICAL: Reference the exact numbers, model names, and performance metrics throughout. Make every insight specific to this unique comparison with these exact results."""
            
            response = self._call_llm(prompt, user_id, 'model_comparison')
            
            # Store insight with unique signature
            insight_data = {
                'user_id': user_id,
                'insight_type': 'model_comparison',
                'content': response,
                'comparison_data': comparison_data,
                'unique_signature': f"{len(models)}_{best_model_name}_{time_signature}",
                'model_used': self.groq_model if self.provider_type == 'groq' else self.provider_type,
                'created_at': datetime.utcnow()
            }
            traffic_insights.insert_one(insight_data)
            
            return {
                'success': True,
                'insight': response,
                'best_model': best_model_name,
                'models_compared': len(models),
                'performance_summary': {
                    'winner': best_model_name,
                    'total_models': len(models),
                    'best_accuracy': best_accuracy if model_analysis else 'N/A',
                    'best_speed': best_speed if model_analysis else 'N/A',
                    'best_vehicle_count': best_vehicles if model_analysis else 0,
                    'winning_factors': winning_summary,
                    'performance_gaps': performance_gaps,
                    'speed_analysis': speed_analysis
                },
                'model_used': self.groq_model if self.provider_type == 'groq' else self.provider_type
            }
            
        except Exception as e:
            logger.error(f"Error comparing model performance: {e}")
            return {
                'success': False,
                'error': str(e),
                'insight': 'Unable to generate model comparison analysis.',
                'model_used': self.provider_type
            }
    
    def describe_scene(self, image_path: str, analysis_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate natural language description of traffic scene
        """
        try:
            # Extract scene information
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            vehicle_count = vehicle_detection.get('total_vehicles', 0)
            vehicle_counts = vehicle_detection.get('vehicle_counts', {})
            scene_type = analysis_data.get('scene_classification', {}).get('scene_type', 'traffic scene')
            
            # Calculate vehicle breakdown
            cars = vehicle_counts.get('cars', 0)
            large_vehicles = vehicle_counts.get('large_vehicles', 0) + vehicle_counts.get('trucks', 0) + vehicle_counts.get('buses', 0)
            two_wheelers = vehicle_counts.get('2_wheelers', 0) + vehicle_counts.get('motorcycles', 0)
            
            # Determine scene characteristics
            if vehicle_count == 0:
                traffic_level = "empty with no visible traffic"
            elif vehicle_count <= 5:
                traffic_level = "quiet with light traffic"
            elif vehicle_count <= 15:
                traffic_level = "moderately busy"
            elif vehicle_count <= 25:
                traffic_level = "busy with heavy traffic"
            else:
                traffic_level = "very congested with dense traffic"
            
            prompt = f"""You are a traffic analyst providing a detailed scene description for traffic management reports. Based on this traffic analysis data, describe what's happening in this traffic scene in clear, professional language:

SCENE ANALYSIS DATA:
- Location Type: {scene_type}
- Total Vehicles Present: {vehicle_count}
- Traffic Level: {traffic_level}
- Vehicle Breakdown:
  * Cars: {cars}
  * Large Vehicles (trucks/buses): {large_vehicles}
  * Two-wheelers (motorcycles/bicycles): {two_wheelers}

Please provide a comprehensive scene description with these elements:

## 📍 SCENE OVERVIEW
Describe the overall traffic situation in this {scene_type}. What is the general activity level and traffic flow condition?

## 🚗 VEHICLE COMPOSITION
Detail the types and numbers of vehicles present:
- Passenger vehicles and their distribution
- Commercial/large vehicles and their impact
- Two-wheelers and their behavior patterns
- Overall traffic mix characteristics

## 🌊 TRAFFIC FLOW ANALYSIS
Describe the traffic flow patterns:
- Movement characteristics
- Density distribution
- Flow efficiency
- Potential bottlenecks or smooth areas

## 🎯 KEY OBSERVATIONS
Highlight the most important aspects of this traffic scene:
- Notable traffic patterns
- Unusual or significant conditions
- Safety considerations
- Management implications

## 📊 QUANTITATIVE SUMMARY
Provide specific numbers and measurements:
- Exact vehicle counts by type
- Traffic density assessment
- Comparative analysis (light/moderate/heavy)

Write in clear, professional language suitable for traffic management reports, city planning documents, and transportation analysis. Focus on observable facts and their practical implications."""
            
            response = self._call_llm(prompt, user_id, 'scene_description')
            
            # Store scene description
            description_data = {
                'user_id': user_id,
                'image_path': image_path,
                'description': response,
                'analysis_data': analysis_data,
                'scene_summary': {
                    'vehicle_count': vehicle_count,
                    'traffic_level': traffic_level,
                    'scene_type': scene_type,
                    'vehicle_breakdown': {
                        'cars': cars,
                        'large_vehicles': large_vehicles,
                        'two_wheelers': two_wheelers
                    }
                },
                'created_at': datetime.utcnow()
            }
            scene_descriptions.insert_one(description_data)
            
            return {
                'success': True,
                'description': response,
                'scene_summary': description_data['scene_summary']
            }
            
        except Exception as e:
            logger.error(f"Error describing scene: {e}")
            return {
                'success': False,
                'error': str(e),
                'description': 'Unable to generate scene description.'
            }
    
    def generate_recommendations(self, analysis_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on traffic analysis
        """
        try:
            # Extract key data
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            vehicle_count = vehicle_detection.get('total_vehicles', 0)
            vehicle_counts = vehicle_detection.get('vehicle_counts', {})
            density = analysis_data.get('traffic_density', {}).get('density_level', 'Unknown')
            scene_type = analysis_data.get('scene_classification', {}).get('scene_type', 'traffic scene')
            
            # Calculate traffic characteristics with specific details
            cars = vehicle_counts.get('cars', 0)
            large_vehicles = vehicle_counts.get('large_vehicles', 0) + vehicle_counts.get('trucks', 0) + vehicle_counts.get('buses', 0)
            two_wheelers = vehicle_counts.get('2_wheelers', 0) + vehicle_counts.get('motorcycles', 0)
            
            # Calculate specific percentages and ratios
            total_vehicles = cars + large_vehicles + two_wheelers
            if total_vehicles > 0:
                car_ratio = cars / total_vehicles
                large_ratio = large_vehicles / total_vehicles
                two_wheeler_ratio = two_wheelers / total_vehicles
            else:
                car_ratio = large_ratio = two_wheeler_ratio = 0
            
            # Determine traffic severity with specific thresholds
            if vehicle_count == 0:
                severity = "No Traffic"
                urgency = "None"
                response_time = "No action needed"
                priority_level = 0
            elif vehicle_count <= 5:
                severity = "Light Traffic"
                urgency = "Low"
                response_time = "Monitor within 4 hours"
                priority_level = 1
            elif vehicle_count <= 15:
                severity = "Moderate Traffic"
                urgency = "Medium"
                response_time = "Review within 2 hours"
                priority_level = 2
            elif vehicle_count <= 25:
                severity = "Heavy Traffic"
                urgency = "High"
                response_time = "Action within 1 hour"
                priority_level = 3
            else:
                severity = "Very Heavy Traffic"
                urgency = "Critical"
                response_time = "Immediate action required"
                priority_level = 4
            
            # Identify specific concerns based on actual data
            specific_concerns = []
            immediate_actions = []
            infrastructure_needs = []
            
            if large_vehicles > cars:
                specific_concerns.append(f"Commercial vehicle dominance ({large_vehicles} vs {cars} cars)")
                immediate_actions.append("Implement truck-specific signal timing")
                infrastructure_needs.append("Consider dedicated truck lanes")
            
            if two_wheelers > 5:
                specific_concerns.append(f"High two-wheeler presence ({two_wheelers} detected)")
                immediate_actions.append("Enhance two-wheeler safety monitoring")
                infrastructure_needs.append("Install motorcycle-specific traffic signals")
            
            if vehicle_count > 20:
                specific_concerns.append(f"Dense traffic conditions ({vehicle_count} vehicles)")
                immediate_actions.append("Activate congestion management protocols")
                infrastructure_needs.append("Evaluate capacity expansion needs")
            
            if car_ratio > 0.8:
                specific_concerns.append(f"Passenger car dominated traffic ({car_ratio:.1%})")
                immediate_actions.append("Optimize signal timing for passenger vehicles")
                infrastructure_needs.append("Consider HOV lane implementation")
            
            # Generate time-sensitive recommendations
            import datetime
            current_time = datetime.datetime.now()
            hour = current_time.hour
            day_of_week = current_time.weekday()  # 0 = Monday
            
            # Time-specific insights
            if 6 <= hour <= 9:
                time_context = "morning rush hour"
                time_recommendations = [
                    "Extend green phases for main arterials",
                    "Deploy traffic enforcement at key intersections",
                    "Activate dynamic message signs for alternate routes"
                ]
            elif 17 <= hour <= 19:
                time_context = "evening rush hour"
                time_recommendations = [
                    "Implement contraflow lanes if available",
                    "Coordinate signal timing across corridor",
                    "Monitor parking restrictions enforcement"
                ]
            elif 10 <= hour <= 16:
                time_context = "midday off-peak"
                time_recommendations = [
                    "Conduct maintenance activities if needed",
                    "Analyze incident-related congestion",
                    "Optimize signal timing for current conditions"
                ]
            else:
                time_context = "off-peak hours"
                time_recommendations = [
                    "Switch to night-time signal patterns",
                    "Monitor for unusual activity patterns",
                    "Schedule maintenance for low-impact periods"
                ]
            
            # Day-specific considerations
            if day_of_week < 5:  # Weekday
                day_context = "weekday"
                day_recommendations = ["Standard commuter traffic protocols", "Business district considerations"]
            else:  # Weekend
                day_context = "weekend"
                day_recommendations = ["Recreational traffic patterns", "Event-related traffic monitoring"]
            
            # Generate unique analysis ID
            analysis_id = f"{vehicle_count}_{cars}_{large_vehicles}_{two_wheelers}_{hour}_{day_of_week}"
            
            prompt = f"""You are a senior traffic management consultant providing specific, actionable recommendations for this EXACT traffic situation. Generate unique recommendations based on these PRECISE conditions:

SPECIFIC TRAFFIC SITUATION REQUIRING RECOMMENDATIONS:
- Exact Location: {scene_type}
- Precise Vehicle Count: {vehicle_count} vehicles
- Detailed Composition: {cars} cars ({car_ratio:.1%}), {large_vehicles} large vehicles ({large_ratio:.1%}), {two_wheelers} two-wheelers ({two_wheeler_ratio:.1%})
- Traffic Severity: {severity}
- Urgency Level: {urgency}
- Response Timeline: {response_time}
- Priority Level: {priority_level}/4
- Time Context: {time_context} on {day_context}
- Analysis ID: {analysis_id}

SPECIFIC CONCERNS IDENTIFIED:
{chr(10).join(f'• {concern}' for concern in specific_concerns) if specific_concerns else '• Standard traffic conditions observed'}

IMMEDIATE ACTIONS REQUIRED:
{chr(10).join(f'• {action}' for action in immediate_actions) if immediate_actions else '• Continue standard monitoring'}

Generate UNIQUE, SPECIFIC recommendations tailored to this exact situation with {vehicle_count} vehicles:

## 🚦 IMMEDIATE ACTIONS (Next 1-4 hours) - Priority Level {priority_level}
Based on {vehicle_count} vehicles with {urgency} urgency, provide specific actions for {time_context}:
- Signal timing adjustments for {cars} cars, {large_vehicles} large vehicles, {two_wheelers} two-wheelers
- Traffic control measures specific to {severity} conditions
- {response_time} response protocols
- Time-specific actions: {', '.join(time_recommendations[:2])}

## 📋 SHORT-TERM STRATEGIES (1-7 days) - {day_context.title()} Focus
Tactical improvements for managing this specific {car_ratio:.1%} cars, {large_ratio:.1%} large vehicles, {two_wheeler_ratio:.1%} two-wheelers mix:
- Pattern monitoring for {vehicle_count}-vehicle scenarios
- Peak hour management for {time_context}
- Route optimization for this vehicle composition
- Day-specific considerations: {', '.join(day_recommendations)}

## 🏗️ INFRASTRUCTURE RECOMMENDATIONS (1-6 months)
Physical improvements needed for {vehicle_count}-vehicle capacity in {scene_type}:
{chr(10).join(f'- {need}' for need in infrastructure_needs) if infrastructure_needs else '- Current infrastructure adequate for observed traffic levels'}
- Capacity planning for {severity} conditions
- Safety infrastructure for {two_wheelers} two-wheelers and {large_vehicles} large vehicles

## 📊 MONITORING & ANALYTICS (Ongoing)
Data collection strategy for this specific traffic pattern:
- Track {vehicle_count}-vehicle scenarios during {time_context}
- Monitor {car_ratio:.1%}/{large_ratio:.1%}/{two_wheeler_ratio:.1%} composition changes
- Performance benchmarks for {severity} conditions
- {day_context.title()} vs weekday comparison metrics

## ⚠️ SAFETY PRIORITIES - {urgency} Risk Level
Address safety concerns for this exact vehicle mix:
- {large_vehicles} large vehicle interaction management
- {two_wheelers} two-wheeler vulnerability mitigation
- {cars} passenger vehicle safety in {severity} conditions
- Specific hazard mitigation for {scene_type}

## 💰 COST-BENEFIT ANALYSIS
Resource allocation for {vehicle_count}-vehicle scenarios:
- High-impact solutions for {severity} traffic
- Priority ranking for {urgency} urgency situations
- ROI analysis for {scene_type} improvements
- Budget allocation for {priority_level}/4 priority level

CRITICAL: Every recommendation must be specific to the exact numbers: {vehicle_count} total vehicles with {cars} cars, {large_vehicles} large vehicles, {two_wheelers} two-wheelers. Reference the specific percentages, urgency level, and time context throughout."""
            
            response = self._call_llm(prompt, user_id, 'recommendations')
            
            # Store insight with unique signature
            insight_data = {
                'user_id': user_id,
                'insight_type': 'traffic_recommendations',
                'content': response,
                'analysis_data': analysis_data,
                'unique_signature': analysis_id,
                'created_at': datetime.utcnow()
            }
            traffic_insights.insert_one(insight_data)
            
            return {
                'success': True,
                'recommendations': response,
                'priority_level': priority_level,
                'traffic_severity': severity,
                'urgency_level': urgency,
                'response_timeline': response_time,
                'key_concerns': specific_concerns,
                'immediate_actions': immediate_actions,
                'infrastructure_needs': infrastructure_needs,
                'time_context': time_context,
                'day_context': day_context,
                'vehicle_breakdown': {
                    'cars': cars,
                    'cars_percentage': car_ratio * 100,
                    'large_vehicles': large_vehicles,
                    'large_vehicles_percentage': large_ratio * 100,
                    'two_wheelers': two_wheelers,
                    'two_wheelers_percentage': two_wheeler_ratio * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': 'Unable to generate recommendations at this time.'
            }
    
    def chat_with_analysis(self, message: str, analysis_context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Interactive chat about traffic analysis results
        """
        try:
            # Get or create conversation session
            session = self._get_or_create_conversation_session(user_id, 'analysis_chat')
            
            # Extract context information
            vehicle_detection = analysis_context.get('vehicle_detection', {})
            vehicle_count = vehicle_detection.get('total_vehicles', 0)
            vehicle_counts = vehicle_detection.get('vehicle_counts', {})
            comparison_table = analysis_context.get('comparison_table', [])
            best_model = analysis_context.get('best_model', 'Unknown')
            
            # Create context-aware prompt
            context_prompt = f"""You are an expert traffic analysis AI assistant helping users understand their traffic analysis results. The user is asking about this specific analysis:

ANALYSIS CONTEXT:
- Total Vehicles Detected: {vehicle_count}
- Vehicle Breakdown: {vehicle_counts}
- AI Models Used: {len(comparison_table)} models compared
- Best Performing Model: {best_model}
- Analysis Type: Comprehensive multi-model comparison

FULL ANALYSIS DATA:
{json.dumps(analysis_context, indent=2)}

USER QUESTION: {message}

Please provide a helpful, accurate, and detailed response based on the analysis data. 

Guidelines for your response:
1. Answer directly and specifically about their analysis results
2. Use the actual numbers and data from their analysis
3. Explain technical concepts in understandable terms
4. Provide actionable insights when relevant
5. If they ask about specific vehicles, models, or metrics, reference the exact data
6. If they ask for recommendations, base them on their specific traffic situation
7. Be conversational but professional
8. If you need to clarify something, ask specific questions about their analysis

Focus on being helpful and informative while staying grounded in their actual analysis results."""
            
            response = self._call_llm(context_prompt, user_id, 'chat')
            
            # Store conversation messages
            llm_messages.insert_one({
                'session_id': str(session['_id']),
                'role': 'user',
                'content': message,
                'timestamp': datetime.utcnow()
            })
            
            llm_messages.insert_one({
                'session_id': str(session['_id']),
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.utcnow()
            })
            
            return {
                'success': True,
                'response': response,
                'session_id': str(session['_id']),
                'context_summary': {
                    'vehicle_count': vehicle_count,
                    'models_compared': len(comparison_table),
                    'best_model': best_model
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': 'Unable to process chat message at this time.'
            }
    
    def _call_llm(self, prompt: str, user_id: str, context_type: str) -> str:
        """
        Make API call to LLM provider - supports multiple free providers
        """
        try:
            # Add uniqueness elements to prompt to ensure different responses
            import datetime
            import random
            
            timestamp = datetime.datetime.now()
            unique_elements = [
                f"Analysis timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Unique analysis ID: {timestamp.microsecond}",
                f"Context variation: {random.randint(1000, 9999)}",
                f"Response seed: {hash(prompt) % 10000}"
            ]
            
            # Enhance prompt with uniqueness instructions
            enhanced_prompt = f"""IMPORTANT: This is a unique analysis request. Generate a completely original response specific to the exact data provided. Do not use generic templates or standard responses.

{chr(10).join(unique_elements)}

{prompt}

CRITICAL INSTRUCTIONS:
- Reference the EXACT numbers and data provided
- Make every sentence specific to this unique situation
- Avoid generic statements that could apply to any traffic analysis
- Use the specific vehicle counts, percentages, and classifications mentioned
- Generate insights that are unique to this particular traffic scenario
- Ensure your response would be different for different input data"""
            
            if self.provider_type == 'ollama':
                return self._call_ollama(enhanced_prompt)
            elif self.provider_type == 'groq' and hasattr(self, 'groq_client'):
                return self._call_groq(enhanced_prompt)
            elif self.provider_type == 'gemini' and hasattr(self, 'gemini_model'):
                return self._call_gemini(enhanced_prompt)
            elif self.provider_type == 'huggingface' and hasattr(self, 'hf_generator'):
                return self._call_huggingface(enhanced_prompt)
            elif self.provider_type == 'openai' and OPENAI_AVAILABLE:
                return self._call_openai(enhanced_prompt)
            else:
                return self._generate_fallback_response(context_type)
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._generate_fallback_response(context_type)
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama local LLM"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": f"You are an expert traffic analysis AI assistant.\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
    
    def _call_groq(self, prompt: str) -> str:
        """Call Groq API with gpt-oss-20b model and fallback support"""
        models_to_try = [
            (self.groq_model, "primary"),
            (self.groq_backup_model, "backup"), 
            (self.groq_fallback_model, "fallback")
        ]
        
        for model, model_type in models_to_try:
            try:
                logger.info(f"Attempting Groq API call with {model_type} model: {model}")
                
                # Create optimized system prompt for traffic analysis
                system_prompt = """You are an expert traffic analysis AI assistant specializing in:
- Vehicle detection and classification analysis
- Traffic flow optimization recommendations  
- Safety assessment and risk evaluation
- Infrastructure planning insights
- Real-time traffic condition interpretation

Provide clear, actionable insights based on traffic data. Be concise but comprehensive."""

                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    model=model,
                    temperature=self.groq_temperature,
                    max_tokens=self.groq_max_tokens,
                    top_p=self.groq_top_p,
                    stream=False
                )
                
                response = chat_completion.choices[0].message.content.strip()
                logger.info(f"Successfully got response from {model_type} model: {model}")
                return response
                
            except Exception as e:
                logger.warning(f"Groq API call failed with {model_type} model {model}: {e}")
                if model_type == "fallback":
                    # If even fallback fails, raise the exception
                    raise
                continue
        
        # This should not be reached, but just in case
        raise Exception("All Groq models failed")
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            full_prompt = f"You are an expert traffic analysis AI assistant.\n\n{prompt}"
            response = self.gemini_model.generate_content(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _call_huggingface(self, prompt: str) -> str:
        """Call Hugging Face local model"""
        try:
            full_prompt = f"You are an expert traffic analysis AI assistant.\n\n{prompt}\n\nResponse:"
            
            result = self.hf_generator(
                full_prompt,
                max_length=len(full_prompt.split()) + 100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )
            
            generated_text = result[0]['generated_text']
            # Extract only the response part
            response = generated_text.split("Response:")[-1].strip()
            return response
            
        except Exception as e:
            logger.error(f"Hugging Face API call failed: {e}")
            raise
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API (legacy support)"""
        try:
            response = openai.ChatCompletion.create(
                model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are an expert traffic analysis AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _generate_fallback_response(self, context_type: str) -> str:
        """
        Generate fallback response when LLM is unavailable
        """
        import datetime
        import random
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        fallbacks = {
            'traffic_analysis': f"""Traffic Analysis Report - {timestamp}

## 🚦 CURRENT TRAFFIC SITUATION
The traffic analysis system has detected vehicles in the uploaded image/video. Due to temporary LLM service unavailability, a detailed AI-powered analysis cannot be generated at this time.

## 📊 DETAILED BREAKDOWN
- Vehicle detection has been completed successfully
- Traffic composition analysis is available in the main results
- Flow characteristics can be observed from the vehicle count data
- Congestion assessment is based on detected vehicle density

## ⚠️ POTENTIAL ISSUES & RISKS
Standard traffic monitoring protocols should be followed based on the vehicle count and composition shown in the main analysis results.

## 💡 RECOMMENDATIONS
- Monitor traffic patterns during similar conditions
- Review vehicle detection results for traffic management decisions
- Consider implementing standard traffic control measures appropriate for the detected vehicle count

## 🎯 KEY INSIGHTS
The analysis has successfully detected and classified vehicles. For detailed AI insights, please try the analysis again when the LLM service is available.

Note: This is a fallback response generated at {timestamp}. The full AI analysis will provide more detailed, specific insights when available.""",

            'feature_insight_vehicle-detection': f"""Vehicle Detection Analysis - {timestamp}

The vehicle detection system has successfully identified and classified vehicles in your traffic scene. The detection algorithms have processed the image and provided accurate vehicle counts and classifications.

Key detection capabilities include identifying cars, large vehicles (trucks and buses), and two-wheelers (motorcycles and bicycles). The system uses advanced computer vision to ensure reliable detection even in complex traffic scenarios.

For detailed AI insights about detection accuracy and vehicle type analysis, please try again when the LLM service is available.""",

            'feature_insight_traffic-density': f"""Traffic Density Analysis - {timestamp}

The traffic density analysis has been completed based on the detected vehicle count and spatial distribution. The system has evaluated congestion levels and flow characteristics for your traffic scene.

Density metrics include vehicle count per area, congestion index calculation, and flow pattern assessment. These measurements help determine current traffic conditions and potential bottlenecks.

For detailed AI insights about density implications and flow recommendations, please try again when the LLM service is available.""",

            'feature_insight_model-comparison': f"""Model Comparison Analysis - {timestamp}

Multiple AI models have been evaluated and compared for accuracy and performance on your traffic scene. The comparison includes detection accuracy, processing speed, and reliability metrics.

The system has ranked the models based on their performance with your specific traffic conditions. Each model's strengths and weaknesses have been assessed to determine the best choice for your analysis.

For detailed AI insights about model selection rationale and performance differences, please try again when the LLM service is available.""",

            'feature_insight_visualization': f"""Visualization Analysis - {timestamp}

The traffic data has been processed and prepared for visual representation through charts, graphs, and interactive displays. The visualization system has organized the vehicle detection results for clear presentation.

Data visualization includes vehicle count charts, composition breakdowns, and traffic flow representations. These visual elements help communicate the analysis results effectively.

For detailed AI insights about visualization effectiveness and recommended improvements, please try again when the LLM service is available.""",

            'feature_insight_history-reports': f"""History & Reports Analysis - {timestamp}

The analysis results have been prepared for historical tracking and report generation. The system has organized the data for long-term storage and comparison with previous analyses.

Report capabilities include data export, trend analysis preparation, and historical comparison features. This enables tracking of traffic patterns over time and generating comprehensive reports.

For detailed AI insights about reporting recommendations and historical analysis value, please try again when the LLM service is available.""",

            'model_comparison': f"""Model Performance Analysis - {timestamp}

## 🏆 BEST PERFORMING MODEL
The model comparison has been completed successfully. Due to temporary LLM service unavailability, detailed performance insights cannot be generated at this time.

## 📊 PERFORMANCE COMPARISON
- Multiple AI models have been evaluated
- Performance metrics are available in the comparison table
- Detection accuracy and speed have been measured
- Model rankings have been determined

## ⚖️ TRADE-OFFS ANALYSIS
Standard trade-offs between speed and accuracy apply. Faster models may have slightly lower accuracy, while more accurate models may take longer to process.

## 🎯 PRACTICAL RECOMMENDATIONS
- Use the highest-ranked model for optimal results
- Consider speed requirements for real-time applications
- Review the detailed comparison table for specific metrics

## 💡 KEY INSIGHTS
Model comparison completed successfully. For detailed AI insights about why specific models performed better, please try again when the LLM service is available.

Note: This is a fallback response generated at {timestamp}.""",

            'scene_description': f"""Traffic Scene Description - {timestamp}

## 📍 SCENE OVERVIEW
The uploaded image/video contains a traffic scene with detected vehicles. Due to temporary LLM service unavailability, a detailed scene description cannot be generated at this time.

## 🚗 VEHICLE COMPOSITION
Vehicle detection has identified multiple vehicle types in the scene. Specific counts and classifications are available in the main analysis results.

## 🌊 TRAFFIC FLOW ANALYSIS
Traffic flow characteristics can be inferred from the vehicle detection results and positioning data.

## 🎯 KEY OBSERVATIONS
The scene analysis has been completed with vehicle detection and classification. For a detailed natural language description, please try again when the LLM service is available.

Note: This is a fallback response generated at {timestamp}.""",

            'recommendations': f"""Traffic Management Recommendations - {timestamp}

## 🚦 IMMEDIATE ACTIONS
Based on the vehicle detection results, standard traffic monitoring and management protocols should be implemented.

## 📋 SHORT-TERM STRATEGIES
- Continue monitoring traffic patterns
- Review vehicle count data for trend analysis
- Implement appropriate traffic control measures

## 🏗️ INFRASTRUCTURE RECOMMENDATIONS
Infrastructure planning should consider the vehicle counts and types detected in this analysis.

## 📊 MONITORING & ANALYTICS
- Track similar traffic conditions
- Monitor vehicle composition changes
- Collect data for pattern analysis

## ⚠️ SAFETY PRIORITIES
Standard safety protocols should be followed based on the detected traffic conditions.

## 💰 COST-BENEFIT ANALYSIS
Resource allocation should be based on the traffic density and composition shown in the analysis results.

Note: This is a fallback response generated at {timestamp}. For detailed, specific recommendations, please try again when the LLM service is available.""",

            'chat': f"""I apologize, but I'm currently unable to provide detailed analysis due to temporary LLM service unavailability. 

Your traffic analysis has been completed successfully, and the vehicle detection results are available in the main interface. 

For detailed AI-powered insights and answers to specific questions about your analysis, please try again in a few moments when the LLM service is restored.

Generated at {timestamp}."""
        }
        
        base_response = fallbacks.get(context_type, "Analysis completed successfully. Detailed insights temporarily unavailable.")
        
        # Add some variation to prevent identical fallback responses
        variation_suffix = f"\n\nService Status: Temporary unavailability - ID {random.randint(1000, 9999)}"
        
        return base_response + variation_suffix
    
    def _get_default_provider(self) -> Optional[Dict[str, Any]]:
        """Get default LLM provider from MongoDB"""
        try:
            return llm_providers.find_one({'is_active': True, 'is_default': True})
        except:
            return None
    
    def _get_or_create_conversation_session(self, user_id: str, context_type: str) -> Dict[str, Any]:
        """Get or create conversation session in MongoDB"""
        session = conversation_sessions.find_one({
            'user_id': user_id,
            'context_type': context_type,
            'is_active': True
        })
        
        if not session:
            provider = self.default_provider
            session_data = {
                'user_id': user_id,
                'provider_id': str(provider['_id']) if provider else None,
                'context_type': context_type,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            result = conversation_sessions.insert_one(session_data)
            session = {**session_data, '_id': result.inserted_id}
        
        return session