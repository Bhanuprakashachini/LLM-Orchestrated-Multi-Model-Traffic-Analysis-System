"""
Traffic Density Analysis Service
Analyzes traffic density and congestion patterns
"""
import numpy as np
import cv2
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class TrafficDensityAnalyzer:
    """
    Analyzes traffic density and congestion patterns
    """
    
    def __init__(self):
        self.density_thresholds = {
            'very_low': 0.1,
            'low': 0.3,
            'medium': 0.5,
            'high': 0.7,
            'very_high': 0.9
        }
    
    def analyze_density(self, detections: List[Dict], image_size: Tuple[int, int]) -> Dict[str, Any]:
        """
        Analyze traffic density based on vehicle detections
        
        Args:
            detections: List of vehicle detections
            image_size: (width, height) of the image
            
        Returns:
            Dictionary containing density analysis
        """
        try:
            width, height = image_size
            image_area = width * height
            
            total_vehicles = len(detections)
            
            if total_vehicles == 0:
                return self._empty_density_result()
            
            # Calculate vehicle density metrics
            vehicle_area = sum(self._calculate_detection_area(det) for det in detections)
            area_coverage = (vehicle_area / image_area) * 100
            
            # Calculate spatial distribution
            positions = [self._get_detection_center(det) for det in detections]
            clustering_factor = self._calculate_clustering(positions, image_size)
            
            # Determine density level
            density_index = self._calculate_density_index(
                total_vehicles, area_coverage, clustering_factor, image_size
            )
            
            density_level = self._get_density_level(density_index)
            
            # Calculate congestion metrics
            congestion_index = min(1.0, density_index)
            flow_state = self._determine_flow_state(congestion_index)
            
            return {
                'density_level': density_level,
                'density_index': density_index,
                'congestion_index': congestion_index,
                'area_coverage_percentage': area_coverage,
                'clustering_factor': clustering_factor,
                'flow_state': flow_state,
                'total_vehicles': total_vehicles,
                'vehicles_per_area': total_vehicles / (image_area / 1000000),  # per million pixels
                'spatial_distribution': self._analyze_spatial_distribution(positions, image_size),
                'density_metrics': {
                    'vehicle_density': total_vehicles / (image_area / 10000),  # per 10k pixels
                    'coverage_ratio': area_coverage / 100,
                    'clustering_score': clustering_factor,
                    'congestion_severity': self._get_congestion_severity(congestion_index)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing traffic density: {e}")
            return self._empty_density_result()
    
    def _calculate_detection_area(self, detection: Dict) -> float:
        """Calculate area of a detection bounding box"""
        try:
            bbox = detection.get('bbox', {})
            width = bbox.get('x2', 0) - bbox.get('x1', 0)
            height = bbox.get('y2', 0) - bbox.get('y1', 0)
            return max(0, width * height)
        except:
            return 0
    
    def _get_detection_center(self, detection: Dict) -> Tuple[float, float]:
        """Get center point of a detection"""
        try:
            bbox = detection.get('bbox', {})
            center_x = (bbox.get('x1', 0) + bbox.get('x2', 0)) / 2
            center_y = (bbox.get('y1', 0) + bbox.get('y2', 0)) / 2
            return (center_x, center_y)
        except:
            return (0, 0)
    
    def _calculate_clustering(self, positions: List[Tuple[float, float]], 
                            image_size: Tuple[int, int]) -> float:
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
    
    def _calculate_density_index(self, vehicle_count: int, area_coverage: float, 
                               clustering_factor: float, image_size: Tuple[int, int]) -> float:
        """Calculate overall density index"""
        try:
            width, height = image_size
            
            # Normalize vehicle count (assume max 100 vehicles for normalization)
            vehicle_factor = min(1.0, vehicle_count / 100.0)
            
            # Normalize area coverage (assume max 30% coverage)
            coverage_factor = min(1.0, area_coverage / 30.0)
            
            # Combine factors with weights
            density_index = (
                vehicle_factor * 0.4 +      # 40% weight on vehicle count
                coverage_factor * 0.4 +     # 40% weight on area coverage
                clustering_factor * 0.2     # 20% weight on clustering
            )
            
            return min(1.0, density_index)
            
        except Exception:
            return 0.0
    
    def _get_density_level(self, density_index: float) -> str:
        """Convert density index to human-readable level"""
        if density_index >= 0.9:
            return 'Very High'
        elif density_index >= 0.7:
            return 'High'
        elif density_index >= 0.5:
            return 'Medium'
        elif density_index >= 0.3:
            return 'Low'
        else:
            return 'Very Low'
    
    def _determine_flow_state(self, congestion_index: float) -> str:
        """Determine traffic flow state based on congestion"""
        if congestion_index >= 0.8:
            return 'Stop-and-Go'
        elif congestion_index >= 0.6:
            return 'Slow Moving'
        elif congestion_index >= 0.3:
            return 'Moderate Flow'
        else:
            return 'Free Flow'
    
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
    
    def _analyze_spatial_distribution(self, positions: List[Tuple[float, float]], 
                                    image_size: Tuple[int, int]) -> str:
        """Analyze the spatial distribution pattern of vehicles"""
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
    
    def _empty_density_result(self) -> Dict[str, Any]:
        """Return empty density analysis result"""
        return {
            'density_level': 'Empty',
            'density_index': 0.0,
            'congestion_index': 0.0,
            'area_coverage_percentage': 0.0,
            'clustering_factor': 0.0,
            'flow_state': 'Free Flow',
            'total_vehicles': 0,
            'vehicles_per_area': 0.0,
            'spatial_distribution': 'Empty',
            'density_metrics': {
                'vehicle_density': 0.0,
                'coverage_ratio': 0.0,
                'clustering_score': 0.0,
                'congestion_severity': 'None'
            }
        }
    
    def calculate_lane_density(self, detections: List[Dict], lane_boundaries: List[Dict]) -> Dict[str, Any]:
        """
        Calculate density for individual lanes
        
        Args:
            detections: List of vehicle detections
            lane_boundaries: List of lane boundary definitions
            
        Returns:
            Dictionary containing per-lane density analysis
        """
        try:
            lane_densities = {}
            
            for i, lane in enumerate(lane_boundaries):
                lane_id = f"lane_{i+1}"
                
                # Find vehicles in this lane
                lane_vehicles = self._filter_vehicles_in_lane(detections, lane)
                
                # Calculate lane-specific metrics
                lane_area = self._calculate_lane_area(lane)
                vehicle_count = len(lane_vehicles)
                
                if lane_area > 0:
                    density = vehicle_count / lane_area
                    coverage = sum(self._calculate_detection_area(v) for v in lane_vehicles) / lane_area
                else:
                    density = 0
                    coverage = 0
                
                lane_densities[lane_id] = {
                    'vehicle_count': vehicle_count,
                    'density': density,
                    'coverage_percentage': coverage * 100,
                    'congestion_level': self._get_lane_congestion_level(density)
                }
            
            return {
                'lane_densities': lane_densities,
                'total_lanes': len(lane_boundaries),
                'average_density': np.mean([ld['density'] for ld in lane_densities.values()]) if lane_densities else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating lane density: {e}")
            return {'lane_densities': {}, 'total_lanes': 0, 'average_density': 0}
    
    def _filter_vehicles_in_lane(self, detections: List[Dict], lane: Dict) -> List[Dict]:
        """Filter vehicles that are within a specific lane"""
        # Simplified implementation - would need actual lane boundary logic
        return detections
    
    def _calculate_lane_area(self, lane: Dict) -> float:
        """Calculate the area of a lane"""
        # Simplified implementation - would need actual lane geometry
        return 10000  # Default lane area
    
    def _get_lane_congestion_level(self, density: float) -> str:
        """Get congestion level for a specific lane"""
        if density >= 0.8:
            return 'Heavy'
        elif density >= 0.5:
            return 'Moderate'
        elif density >= 0.2:
            return 'Light'
        else:
            return 'Free'