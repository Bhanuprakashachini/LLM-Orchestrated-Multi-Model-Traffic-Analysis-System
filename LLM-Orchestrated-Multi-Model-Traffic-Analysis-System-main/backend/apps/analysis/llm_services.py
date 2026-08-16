"""
LLM-based services for intelligent traffic analysis
"""
import json
from typing import Dict, Any, List


class TrafficLLMService:
    """
    LLM-based service for intelligent traffic analysis and natural language processing
    """
    
    def __init__(self):
        self.model_name = "Traffic Analysis LLM"
        
    def generate_traffic_explanation(self, traffic_data: Dict[str, Any]) -> str:
        """
        8️⃣ Generate human-readable explanation of traffic conditions
        """
        total_vehicles = traffic_data.get('total_vehicles', 0)
        density_level = traffic_data.get('density_level', 'Unknown')
        congestion_index = traffic_data.get('congestion_index', 0)
        vehicle_counts = traffic_data.get('vehicle_counts', {})
        
        # Generate intelligent explanation
        explanation = f"Traffic Analysis Summary:\n\n"
        
        if total_vehicles == 0:
            explanation += "The road appears to be completely empty with no vehicles detected. This indicates very light traffic conditions, possibly during off-peak hours."
        elif total_vehicles <= 5:
            explanation += f"Light traffic detected with {total_vehicles} vehicles present. The road has good flow with minimal congestion."
        elif total_vehicles <= 15:
            explanation += f"Moderate traffic observed with {total_vehicles} vehicles. The density level is {density_level} with a congestion index of {congestion_index:.2f}."
        elif total_vehicles <= 25:
            explanation += f"Heavy traffic conditions with {total_vehicles} vehicles detected. The {density_level} density may cause slower movement and potential delays."
        else:
            explanation += f"Severe congestion detected with {total_vehicles} vehicles. This {density_level} traffic density (index: {congestion_index:.2f}) indicates significant delays and slow-moving traffic."
        
        # Add vehicle composition analysis
        if vehicle_counts:
            explanation += f"\n\nVehicle Composition:\n"
            for vehicle_type, count in vehicle_counts.items():
                if count > 0:
                    percentage = (count / total_vehicles) * 100 if total_vehicles > 0 else 0
                    explanation += f"- {vehicle_type.capitalize()}: {count} ({percentage:.1f}%)\n"
        
        # Add impact assessment
        if congestion_index >= 0.8:
            explanation += "\nImpact: Expect significant delays and consider alternative routes."
        elif congestion_index >= 0.6:
            explanation += "\nImpact: Moderate delays expected, allow extra travel time."
        elif congestion_index >= 0.3:
            explanation += "\nImpact: Normal traffic flow with minor delays possible."
        else:
            explanation += "\nImpact: Excellent traffic conditions for smooth travel."
            
        return explanation
    
    def analyze_model_comparison(self, comparison_data: Dict[str, Any]) -> str:
        """
        9️⃣ Analyze and explain model comparison results
        """
        yolov8_data = comparison_data.get('yolov8', {})
        yolov12_data = comparison_data.get('yolov12', {})
        best_model = comparison_data.get('best_model', 'Unknown')
        
        analysis = "Model Performance Comparison Analysis:\n\n"
        
        # Detection accuracy comparison
        yolov8_vehicles = yolov8_data.get('total_vehicles', 0)
        yolov12_vehicles = yolov12_data.get('total_vehicles', 0)
        
        analysis += f"Detection Results:\n"
        analysis += f"- YOLOv8: {yolov8_vehicles} vehicles detected\n"
        analysis += f"- YOLOv12: {yolov12_vehicles} vehicles detected\n"
        
        # Confidence comparison
        yolov8_conf = yolov8_data.get('confidence', 0)
        yolov12_conf = yolov12_data.get('confidence', 0)
        
        analysis += f"\nConfidence Scores:\n"
        analysis += f"- YOLOv8: {yolov8_conf:.3f}\n"
        analysis += f"- YOLOv12: {yolov12_conf:.3f}\n"
        
        # Performance comparison
        yolov8_fps = yolov8_data.get('fps', 0)
        yolov12_fps = yolov12_data.get('fps', 0)
        
        analysis += f"\nProcessing Speed:\n"
        analysis += f"- YOLOv8: {yolov8_fps:.1f} FPS\n"
        analysis += f"- YOLOv12: {yolov12_fps:.1f} FPS\n"
        
        # Recommendation
        analysis += f"\nRecommendation:\n"
        analysis += f"Based on the analysis, {best_model} is selected as the optimal model. "
        
        if best_model == "YOLOv12":
            if yolov12_conf > yolov8_conf:
                analysis += "YOLOv12 shows higher confidence scores, indicating more reliable detections."
            elif yolov12_vehicles > yolov8_vehicles:
                analysis += "YOLOv12 detected more vehicles, suggesting better sensitivity."
        else:
            if yolov8_fps > yolov12_fps:
                analysis += "YOLOv8 offers better processing speed for real-time applications."
                
        return analysis
    
    def generate_traffic_summary(self, traffic_data: Dict[str, Any]) -> str:
        """
        🔟 Generate concise traffic summary
        """
        total_vehicles = traffic_data.get('total_vehicles', 0)
        density_level = traffic_data.get('density_level', 'Unknown')
        congestion_index = traffic_data.get('congestion_index', 0)
        vehicle_dist = traffic_data.get('vehicle_distribution', {})
        
        # Generate concise summary
        summary = f"Traffic Summary: {density_level} density with {total_vehicles} vehicles detected. "
        
        if congestion_index >= 0.8:
            summary += "Heavy congestion present - expect significant delays."
        elif congestion_index >= 0.6:
            summary += "Moderate congestion - allow extra travel time."
        elif congestion_index >= 0.3:
            summary += "Light traffic - normal flow conditions."
        else:
            summary += "Clear roads - optimal travel conditions."
        
        # Add dominant vehicle type
        if vehicle_dist:
            max_type = max(vehicle_dist.items(), key=lambda x: x[1])
            if max_type[1] > 0:
                summary += f" Predominantly {max_type[0]} ({max_type[1]} units)."
        
        return summary
    
    def generate_recommendations(self, traffic_data: Dict[str, Any]) -> str:
        """
        1️⃣1️⃣ Generate actionable traffic management recommendations
        """
        congestion_level = traffic_data.get('congestion_level', 'Unknown')
        peak_hours = traffic_data.get('peak_hours', False)
        weather = traffic_data.get('weather', 'Unknown')
        incidents = traffic_data.get('incidents', [])
        
        recommendations = "Traffic Management Recommendations:\n\n"
        
        # Congestion-based recommendations
        if congestion_level == "High":
            recommendations += "🚦 Immediate Actions:\n"
            recommendations += "- Activate dynamic traffic signal timing\n"
            recommendations += "- Deploy traffic management personnel\n"
            recommendations += "- Consider opening additional lanes\n"
            recommendations += "- Issue traffic advisories to commuters\n\n"
        elif congestion_level == "Medium":
            recommendations += "⚠️ Preventive Measures:\n"
            recommendations += "- Monitor traffic flow closely\n"
            recommendations += "- Prepare contingency plans\n"
            recommendations += "- Optimize signal timing\n\n"
        else:
            recommendations += "✅ Maintenance Window:\n"
            recommendations += "- Good time for road maintenance\n"
            recommendations += "- Consider infrastructure inspections\n\n"
        
        # Peak hours recommendations
        if peak_hours:
            recommendations += "🕐 Peak Hour Strategies:\n"
            recommendations += "- Implement rush hour lane management\n"
            recommendations += "- Increase public transport frequency\n"
            recommendations += "- Encourage flexible work hours\n\n"
        
        # Weather-based recommendations
        if weather in ["Rain", "Snow", "Fog"]:
            recommendations += "🌧️ Weather Considerations:\n"
            recommendations += "- Reduce speed limits\n"
            recommendations += "- Increase following distance advisories\n"
            recommendations += "- Deploy additional safety personnel\n\n"
        
        # Incident-based recommendations
        if incidents:
            recommendations += "🚨 Incident Response:\n"
            recommendations += "- Activate emergency response protocols\n"
            recommendations += "- Implement traffic diversions\n"
            recommendations += "- Coordinate with emergency services\n"
        
        return recommendations
    
    def handle_natural_query(self, query: str, traffic_context: Dict[str, Any]) -> str:
        """
        1️⃣2️⃣ Handle natural language queries about traffic
        """
        query_lower = query.lower()
        total_vehicles = traffic_context.get('total_vehicles', 0)
        density_level = traffic_context.get('density_level', 'Unknown')
        lanes = traffic_context.get('lanes', {})
        
        # Query pattern matching and response generation
        if "congested" in query_lower or "congestion" in query_lower:
            if total_vehicles >= 25:
                return f"Yes, the road is quite congested with {total_vehicles} vehicles detected. The traffic density is {density_level}."
            elif total_vehicles >= 15:
                return f"There is moderate congestion with {total_vehicles} vehicles. Traffic is moving but slower than usual."
            else:
                return f"No significant congestion detected. Only {total_vehicles} vehicles present with {density_level} density."
        
        elif "lane" in query_lower and "maximum" in query_lower:
            if lanes:
                max_lane = max(lanes.items(), key=lambda x: x[1])
                return f"The {max_lane[0]} lane has the maximum traffic with {max_lane[1]} vehicles."
            else:
                return "Lane-specific data is not available for this analysis."
        
        elif "vehicle count" in query_lower or "how many" in query_lower:
            return f"Currently, there are {total_vehicles} vehicles detected in the analyzed area."
        
        elif "good time" in query_lower or "travel" in query_lower:
            if total_vehicles <= 10:
                return "Yes, this appears to be a good time to travel with light traffic conditions."
            elif total_vehicles <= 20:
                return "Traffic is moderate. It's an acceptable time to travel but expect some delays."
            else:
                return "This might not be the best time to travel due to heavy traffic. Consider waiting or using alternative routes."
        
        elif "speed" in query_lower:
            if density_level == "High":
                return "Traffic speed is likely reduced due to high density. Expect slower movement."
            elif density_level == "Medium":
                return "Traffic speed is moderate with some slowdowns possible."
            else:
                return "Traffic speed should be normal with good flow conditions."
        
        else:
            # Generic response for unrecognized queries
            return f"Based on current analysis: {total_vehicles} vehicles detected with {density_level} traffic density. Please ask specific questions about congestion, vehicle counts, or travel conditions."