"""
Helmet Detection Service for Motorcycles
Implements multiple detection methods for enhanced accuracy
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class HelmetDetector:
    """Advanced helmet detection for motorcycle riders"""
    
    def __init__(self):
        self.helmet_cascade = None
        self.load_cascade_classifier()
    
    def load_cascade_classifier(self):
        """Load Haar cascade for helmet detection (if available)"""
        try:
            # Try to load a helmet cascade classifier
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'
            self.helmet_cascade = cv2.CascadeClassifier(cascade_path)
        except:
            self.helmet_cascade = None
    
    def detect_person_on_motorcycle(self, motorcycle_region: np.ndarray) -> bool:
        """
        Detect if there's actually a person riding the motorcycle
        Returns True if person detected, False if empty motorcycle
        """
        try:
            if motorcycle_region.size == 0:
                return False
            
            # Method 1: Look for human-like shapes and colors
            person_score = 0.0
            
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(motorcycle_region, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(motorcycle_region, cv2.COLOR_BGR2HSV)
            
            # Look for skin tones (face/hands)
            skin_lower = np.array([0, 20, 70], dtype=np.uint8)
            skin_upper = np.array([20, 255, 255], dtype=np.uint8)
            skin_mask = cv2.inRange(hsv, skin_lower, skin_upper)
            skin_pixels = cv2.countNonZero(skin_mask)
            total_pixels = motorcycle_region.shape[0] * motorcycle_region.shape[1]
            
            if total_pixels > 0:
                skin_ratio = skin_pixels / total_pixels
                if skin_ratio > 0.02:  # At least 2% skin-colored pixels
                    person_score += 0.3
            
            # Look for clothing colors (non-metallic colors)
            clothing_colors = [
                # Red clothing
                ([0, 100, 100], [10, 255, 255]),
                # Blue clothing  
                ([100, 100, 100], [130, 255, 255]),
                # Green clothing
                ([40, 100, 100], [80, 255, 255]),
                # Yellow clothing
                ([20, 100, 100], [30, 255, 255]),
                # Purple clothing
                ([130, 100, 100], [160, 255, 255])
            ]
            
            clothing_pixels = 0
            for lower, upper in clothing_colors:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                clothing_pixels += cv2.countNonZero(mask)
            
            if total_pixels > 0:
                clothing_ratio = clothing_pixels / total_pixels
                if clothing_ratio > 0.05:  # At least 5% clothing-colored pixels
                    person_score += 0.2
            
            # Look for human-like contours (head, torso shapes)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            human_like_contours = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 200:  # Minimum area for human parts
                    # Check aspect ratio for human-like shapes
                    x, y, w, h = cv2.boundingRect(contour)
                    if h > 0:
                        aspect_ratio = w / h
                        # Human torso/head typically has aspect ratio between 0.3 and 2.0
                        if 0.3 < aspect_ratio < 2.0:
                            human_like_contours += 1
            
            if human_like_contours >= 2:  # At least 2 human-like shapes
                person_score += 0.3
            
            # Look for texture complexity (humans have more complex textures than empty bikes)
            texture_std = np.std(gray)
            if texture_std > 30:  # Higher texture variation suggests person
                person_score += 0.2
            
            # Final decision - require at least 40% confidence for person detection
            has_person = person_score > 0.4
            
            print(f"👤 Person detection: Score={person_score:.2f}, HasPerson={has_person}")
            
            return has_person
            
        except Exception as e:
            print(f"❌ Person detection error: {e}")
            return False  # Default to no person if detection fails

    def detect_helmet_multi_method(self, frame: np.ndarray, motorcycle_bbox: List[float]) -> Dict:
        """
        Detect helmet using multiple methods for enhanced accuracy
        Returns detection result with confidence score
        """
        x1, y1, x2, y2 = motorcycle_bbox
        
        # Extract motorcycle region
        motorcycle_region = frame[int(y1):int(y2), int(x1):int(x2)]
        
        if motorcycle_region.size == 0:
            return {'has_helmet': False, 'confidence': 0.0, 'method': 'invalid_region'}
        
        # Method 1: Color Analysis
        color_result = self._detect_helmet_by_color(motorcycle_region)
        
        # Method 2: Shape Detection
        shape_result = self._detect_helmet_by_shape(motorcycle_region)
        
        # Method 3: Texture Analysis
        texture_result = self._detect_helmet_by_texture(motorcycle_region)
        
        # Method 4: Contour Detection
        contour_result = self._detect_helmet_by_contours(motorcycle_region)
        
        # Method 5: Hair/Skin Analysis (negative detection)
        hair_skin_result = self._detect_hair_skin(motorcycle_region)
        
        # Method 6: Edge Detection
        edge_result = self._detect_helmet_by_edges(motorcycle_region)
        
        # Combine results using weighted voting
        methods = [
            ('color', color_result, 0.2),
            ('shape', shape_result, 0.15),
            ('texture', texture_result, 0.15),
            ('contour', contour_result, 0.2),
            ('hair_skin', hair_skin_result, 0.15),
            ('edge', edge_result, 0.15)
        ]
        
        total_confidence = 0.0
        helmet_votes = 0
        no_helmet_votes = 0
        total_weight = 0.0
        
        for method_name, result, weight in methods:
            if result['confidence'] > 0.2:  # Lower threshold for more detections
                total_confidence += result['confidence'] * weight
                if result['has_helmet']:
                    helmet_votes += weight
                else:
                    no_helmet_votes += weight
                total_weight += weight
        
        # Final decision - be more aggressive about detecting no helmet
        if total_weight > 0:
            final_confidence = total_confidence / total_weight
            # Require strong evidence for helmet detection (80% confidence)
            has_helmet = helmet_votes > (total_weight * 0.8)  # Increased from 0.7 to 0.8
        else:
            # Default to no helmet if no confident detections (more realistic for motorcycles)
            has_helmet = False
            final_confidence = 0.7  # Higher confidence for no helmet default
        
        return {
            'has_helmet': has_helmet,
            'confidence': final_confidence,
            'method': 'multi_method_ensemble',
            'individual_results': {
                method_name: result for method_name, result, _ in methods
            }
        }
    
    def _detect_helmet_by_color(self, region: np.ndarray) -> Dict:
        """Detect helmet based on color analysis - improved to detect hair/skin vs helmet"""
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
            
            # Define helmet color ranges (common helmet colors)
            helmet_colors = [
                # Black helmets
                ([0, 0, 0], [180, 255, 50]),
                # White helmets  
                ([0, 0, 200], [180, 30, 255]),
                # Red helmets
                ([0, 120, 70], [10, 255, 255]),
                # Blue helmets
                ([100, 150, 0], [130, 255, 255]),
                # Yellow helmets
                ([20, 100, 100], [30, 255, 255])
            ]
            
            # Define hair/skin color ranges (indicates NO helmet)
            hair_skin_colors = [
                # Skin tones
                ([0, 20, 70], [20, 255, 255]),
                # Brown hair
                ([10, 50, 20], [20, 255, 200]),
                # Black hair (different from helmet black - more saturated)
                ([0, 0, 0], [180, 255, 80]),
                # Blonde hair
                ([15, 30, 100], [35, 255, 255])
            ]
            
            total_pixels = region.shape[0] * region.shape[1]
            helmet_pixels = 0
            hair_skin_pixels = 0
            
            # Count helmet-colored pixels
            for lower, upper in helmet_colors:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                helmet_pixels += cv2.countNonZero(mask)
            
            # Count hair/skin-colored pixels
            for lower, upper in hair_skin_colors:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                hair_skin_pixels += cv2.countNonZero(mask)
            
            # Calculate ratios
            helmet_ratio = helmet_pixels / total_pixels if total_pixels > 0 else 0
            hair_skin_ratio = hair_skin_pixels / total_pixels if total_pixels > 0 else 0
            
            # Decision logic - prioritize hair/skin detection for no helmet
            if hair_skin_ratio > 0.15:  # Significant hair/skin detected
                has_helmet = False
                confidence = min(hair_skin_ratio * 4, 1.0)  # High confidence for no helmet
            elif helmet_ratio > 0.20:  # Strong helmet color presence
                has_helmet = True
                confidence = min(helmet_ratio * 3, 1.0)
            else:
                # Unclear - default to no helmet (more conservative)
                has_helmet = False
                confidence = 0.5
            
            return {'has_helmet': has_helmet, 'confidence': confidence}
            
        except Exception:
            return {'has_helmet': False, 'confidence': 0.0}
    
    def _detect_helmet_by_shape(self, region: np.ndarray) -> Dict:
        """Detect helmet based on shape analysis"""
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            helmet_score = 0.0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    # Calculate roundness (helmet-like shape)
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        roundness = 4 * np.pi * area / (perimeter * perimeter)
                        
                        # Helmets are relatively round
                        if 0.3 < roundness < 0.9:
                            helmet_score += roundness
            
            has_helmet = helmet_score > 0.4
            confidence = min(helmet_score, 1.0)
            
            return {'has_helmet': has_helmet, 'confidence': confidence}
            
        except Exception:
            return {'has_helmet': False, 'confidence': 0.0}
    
    def _detect_helmet_by_texture(self, region: np.ndarray) -> Dict:
        """Detect helmet based on texture analysis"""
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Calculate texture using standard deviation
            mean = np.mean(gray)
            std = np.std(gray)
            
            # Helmets typically have more uniform texture than hair
            texture_uniformity = 1.0 - (std / 255.0) if std > 0 else 0.0
            
            # High uniformity suggests helmet
            has_helmet = texture_uniformity > 0.6
            confidence = texture_uniformity
            
            return {'has_helmet': has_helmet, 'confidence': confidence}
            
        except Exception:
            return {'has_helmet': False, 'confidence': 0.0}
    
    def _detect_helmet_by_contours(self, region: np.ndarray) -> Dict:
        """Detect helmet using contour analysis"""
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Threshold to get binary image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return {'has_helmet': False, 'confidence': 0.0}
            
            # Get largest contour (likely the main object)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            if area < 50:
                return {'has_helmet': False, 'confidence': 0.0}
            
            # Calculate aspect ratio
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = w / h if h > 0 else 0
            
            # Helmets typically have aspect ratio close to 1 (round-ish)
            helmet_like_ratio = 1.0 - abs(aspect_ratio - 1.0)
            helmet_like_ratio = max(0, helmet_like_ratio)
            
            has_helmet = helmet_like_ratio > 0.5 and area > 200
            confidence = helmet_like_ratio
            
            return {'has_helmet': has_helmet, 'confidence': confidence}
            
        except Exception:
            return {'has_helmet': False, 'confidence': 0.0}
    
    def _detect_hair_skin(self, region: np.ndarray) -> Dict:
        """Detect hair/skin (negative indicator for helmet)"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
            
            # Skin color ranges
            skin_lower = np.array([0, 20, 70])
            skin_upper = np.array([20, 255, 255])
            skin_mask = cv2.inRange(hsv, skin_lower, skin_upper)
            
            # Hair color ranges (dark colors)
            hair_lower = np.array([0, 0, 0])
            hair_upper = np.array([180, 255, 40])
            hair_mask = cv2.inRange(hsv, hair_lower, hair_upper)
            
            total_pixels = region.shape[0] * region.shape[1]
            skin_pixels = cv2.countNonZero(skin_mask)
            hair_pixels = cv2.countNonZero(hair_mask)
            
            skin_ratio = skin_pixels / total_pixels if total_pixels > 0 else 0
            hair_ratio = hair_pixels / total_pixels if total_pixels > 0 else 0
            
            # High skin/hair ratio suggests no helmet
            no_helmet_confidence = (skin_ratio + hair_ratio) * 2
            no_helmet_confidence = min(no_helmet_confidence, 1.0)
            
            has_helmet = no_helmet_confidence < 0.4
            confidence = 1.0 - no_helmet_confidence if has_helmet else no_helmet_confidence
            
            return {'has_helmet': has_helmet, 'confidence': confidence}
            
        except Exception:
            return {'has_helmet': False, 'confidence': 0.0}
    
    def _detect_helmet_by_edges(self, region: np.ndarray) -> Dict:
        """Detect helmet using edge analysis"""
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 30, 100)
            
            # Count edge pixels
            edge_pixels = cv2.countNonZero(edges)
            total_pixels = region.shape[0] * region.shape[1]
            edge_ratio = edge_pixels / total_pixels if total_pixels > 0 else 0
            
            # Helmets have moderate edge density (not too smooth, not too complex)
            optimal_edge_ratio = 0.1  # Optimal edge ratio for helmets
            edge_score = 1.0 - abs(edge_ratio - optimal_edge_ratio) / optimal_edge_ratio
            edge_score = max(0, edge_score)
            
            has_helmet = edge_score > 0.5 and 0.05 < edge_ratio < 0.2
            confidence = edge_score
            
            return {'has_helmet': has_helmet, 'confidence': confidence}
            
        except Exception:
            return {'has_helmet': False, 'confidence': 0.0}
    
    def annotate_helmet_detection(self, frame: np.ndarray, motorcycle_bbox: List[float], 
                                 helmet_result: Dict) -> np.ndarray:
        """Annotate frame with helmet detection results"""
        x1, y1, x2, y2 = motorcycle_bbox
        
        if helmet_result['has_helmet']:
            # Green for helmet detected
            color = (0, 255, 0)
            text = f"HELMET OK ({helmet_result['confidence']:.2f})"
        else:
            # Orange/Red for no helmet
            color = (0, 165, 255)  # Orange
            text = f"NO HELMET! ({helmet_result['confidence']:.2f})"
        
        # Draw helmet status
        cv2.putText(frame, text, (int(x1), int(y2) + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame
    
    def create_helmet_violation(self, motorcycle_detection: Dict, helmet_result: Dict, 
                              frame_number: int, timestamp: str) -> Optional[Dict]:
        """Create a helmet violation record if no helmet detected"""
        if not helmet_result['has_helmet'] and helmet_result['confidence'] > 0.5:
            return {
                'type': 'NO_HELMET',
                'vehicle_type': 'motorcycle',
                'confidence': helmet_result['confidence'],
                'detection_method': helmet_result['method'],
                'bbox': motorcycle_detection['bbox'],
                'frame_number': frame_number,
                'timestamp': timestamp,
                'details': {
                    'detection_confidence': motorcycle_detection['confidence'],
                    'helmet_confidence': helmet_result['confidence'],
                    'individual_methods': helmet_result.get('individual_results', {})
                }
            }
        return None