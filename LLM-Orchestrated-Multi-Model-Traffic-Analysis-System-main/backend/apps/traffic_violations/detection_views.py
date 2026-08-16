"""
Traffic Violations Detection Views - Core Implementation
Implements the same functionality as guaranteed_speed_system.py
"""

import os
import json
import base64
import threading
import time
import queue
from datetime import datetime
from typing import Dict, Optional

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Try to import CV2 and YOLO, fallback gracefully if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not available - detection will be limited")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ Ultralytics YOLO not available - detection will be limited")

# Import the updated speed calculator from services
from .services.guaranteed_speed_calculator import GuaranteedSpeedCalculator
from .services.helmet_detector import HelmetDetector
from collections import defaultdict, deque

# Global variables for detection state
detection_state = {
    'is_detecting': False,
    'detection_thread': None,
    'current_settings': {
        'speed_limit': 50,
        'model_name': 'yolov8s',
        'confidence_threshold': 0.15,  # Lowered for better detection
        'video_path': '',
        'video_source_type': 'file'
    },
    'frame_queue': queue.Queue(maxsize=1),
    'violation_queue': queue.Queue(maxsize=10),
    'model': None,
    'speed_calculator': None,
    'helmet_detector': None
}

# Statistics
violation_stats = {
    'total_violations': 0,
    'speed_violations': 0,
    'helmet_violations': 0,
    'recent_violations': [],
    'vehicle_counts': {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_video(request):
    """Handle video file upload"""
    try:
        if 'video' not in request.FILES:
            return Response({
                'status': 'error',
                'message': 'No video file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['video']
        
        if uploaded_file.name == '':
            return Response({
                'status': 'error',
                'message': 'No file selected'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file extension
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            return Response({
                'status': 'error',
                'message': f'Unsupported file format. Supported: {", ".join(allowed_extensions)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size (500MB limit)
        max_size = 500 * 1024 * 1024  # 500MB
        if uploaded_file.size > max_size:
            return Response({
                'status': 'error',
                'message': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the file
        upload_dir = 'traffic_violations_data/uploaded_videos'
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Save file
        with open(file_path, 'wb') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        file_size = uploaded_file.size / (1024 * 1024)  # MB
        
        return Response({
            'status': 'success',
            'message': f'Video uploaded successfully: {uploaded_file.name}',
            'file_path': file_path,
            'file_name': safe_filename,
            'file_size': f"{file_size:.1f} MB"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Upload failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_videos(request):
    """Get available video files"""
    try:
        videos = []
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')
        
        # Check uploaded videos directory first
        upload_dir = 'traffic_violations_data/uploaded_videos'
        if os.path.exists(upload_dir):
            try:
                for file in os.listdir(upload_dir):
                    if file.lower().endswith(video_extensions):
                        full_path = os.path.join(upload_dir, file)
                        file_size = os.path.getsize(full_path) / (1024 * 1024)
                        videos.append({
                            'name': file,
                            'path': full_path,
                            'size': f"{file_size:.1f} MB",
                            'location': 'Uploaded Videos',
                            'created_at': datetime.fromtimestamp(os.path.getctime(full_path)).isoformat()
                        })
            except Exception as e:
                print(f"Error scanning upload directory: {e}")
        
        # Check current directory
        try:
            for file in os.listdir('.'):
                if file.lower().endswith(video_extensions):
                    file_size = os.path.getsize(file) / (1024 * 1024)
                    videos.append({
                        'name': file,
                        'path': file,
                        'size': f"{file_size:.1f} MB",
                        'location': 'Current Directory',
                        'created_at': datetime.fromtimestamp(os.path.getctime(file)).isoformat()
                    })
        except Exception as e:
            print(f"Error scanning current directory: {e}")
        
        # Check Traffic detection system folder
        traffic_dir = 'Traffic detection system'
        if os.path.exists(traffic_dir):
            try:
                for file in os.listdir(traffic_dir):
                    if file.lower().endswith(video_extensions):
                        full_path = os.path.join(traffic_dir, file)
                        file_size = os.path.getsize(full_path) / (1024 * 1024)
                        videos.append({
                            'name': file,
                            'path': full_path,
                            'size': f"{file_size:.1f} MB",
                            'location': 'Traffic Detection System',
                            'created_at': datetime.fromtimestamp(os.path.getctime(full_path)).isoformat()
                        })
            except Exception as e:
                print(f"Error scanning traffic directory: {e}")
        
        # Sort by creation time (newest first)
        videos.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return Response({
            'videos': videos,
            'count': len(videos),
            'message': f"Found {len(videos)} video files" if videos else "No video files found"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to list videos: {str(e)}',
            'videos': [],
            'count': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def handle_settings(request):
    """Handle detection settings"""
    global detection_state
    
    if request.method == 'POST':
        try:
            data = request.data
            detection_state['current_settings'].update(data)
            
            return Response({
                'status': 'success',
                'settings': detection_state['current_settings']
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(detection_state['current_settings'], status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_detection(request):
    """Start traffic violation detection - FULL IMPLEMENTATION"""
    global detection_state, violation_stats
    
    try:
        if not CV2_AVAILABLE or not YOLO_AVAILABLE:
            return Response({
                'status': 'error',
                'message': 'Detection dependencies not available. Please install opencv-python and ultralytics.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if detection_state['is_detecting']:
            return Response({
                'status': 'error',
                'message': 'Detection already running'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get video path from request or settings
        video_path = request.data.get('video_path', detection_state['current_settings']['video_path'])
        
        if not video_path:
            return Response({
                'status': 'error',
                'message': 'No video path specified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not os.path.exists(video_path):
            return Response({
                'status': 'error',
                'message': f'Video file not found: {video_path}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update settings
        detection_state['current_settings']['video_path'] = video_path
        
        # Load YOLO model
        if detection_state['model'] is None:
            print(f"🤖 Loading {detection_state['current_settings']['model_name']} model...")
            try:
                model_name = detection_state['current_settings']['model_name']
                model_file = f"{model_name}.pt"
                
                # Use centralized models directory
                centralized_model_path = os.path.join('backend', 'models', model_file)
                
                if os.path.exists(centralized_model_path):
                    detection_state['model'] = YOLO(centralized_model_path)
                    print(f"✅ Model loaded from centralized location: {centralized_model_path}")
                else:
                    # Let YOLO download the model
                    detection_state['model'] = YOLO(model_file)
                    print(f"✅ Model downloaded: {model_file}")
                    
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': f'Failed to load YOLO model: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Initialize speed calculator
        if detection_state['speed_calculator'] is None:
            detection_state['speed_calculator'] = GuaranteedSpeedCalculator()
        
        # Initialize helmet detector
        if detection_state['helmet_detector'] is None:
            detection_state['helmet_detector'] = HelmetDetector()
        
        # Reset statistics
        violation_stats.update({
            'total_violations': 0,
            'speed_violations': 0,
            'helmet_violations': 0,
            'recent_violations': [],
            'vehicle_counts': {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
        })
        
        # Start detection thread
        detection_state['is_detecting'] = True
        detection_state['detection_thread'] = threading.Thread(
            target=guaranteed_speed_detection_worker,
            daemon=True
        )
        detection_state['detection_thread'].start()
        
        return Response({
            'status': 'success',
            'message': f'Traffic violation detection started with {detection_state["current_settings"]["model_name"]} - ALL vehicles will show speeds!',
            'settings': detection_state['current_settings']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        detection_state['is_detecting'] = False
        return Response({
            'status': 'error',
            'message': f'Failed to start detection: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_detection(request):
    """Stop traffic violation detection"""
    global detection_state
    
    detection_state['is_detecting'] = False
    
    return Response({
        'status': 'success',
        'message': 'Detection stopped'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_frame(request):
    """Get current frame with annotations"""
    try:
        if not detection_state['frame_queue'].empty():
            frame_data = detection_state['frame_queue'].get_nowait()
            print(f"📡 Sending frame data: image={bool(frame_data.get('image'))}, stats={bool(frame_data.get('stats'))}")
            return Response(frame_data, status=status.HTTP_200_OK)
        else:
            # Return empty response if no frame available
            print("📡 No frame available in queue")
            return Response({
                'image': None,
                'stats': violation_stats
            }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"❌ Frame endpoint error: {e}")
        return Response({
            'image': None,
            'stats': {},
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_violations(request):
    """Get recent violations"""
    try:
        violations = []
        
        # Get violations from queue
        while not detection_state['violation_queue'].empty():
            try:
                violations.append(detection_state['violation_queue'].get_nowait())
            except queue.Empty:
                break
        
        return Response({
            'violations': violations,
            'stats': violation_stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'violations': [],
            'stats': {},
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_statistics(request):
    """Get current session statistics"""
    try:
        return Response(violation_stats, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_session(request):
    """Reset current detection session"""
    global violation_stats, detection_state
    
    try:
        # Reset statistics
        violation_stats.update({
            'total_violations': 0,
            'speed_violations': 0,
            'helmet_violations': 0,
            'recent_violations': [],
            'vehicle_counts': {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
        })
        
        # Reset speed calculator
        if detection_state['speed_calculator']:
            detection_state['speed_calculator'].reset_tracking()
        
        # Clear queues
        while not detection_state['frame_queue'].empty():
            try:
                detection_state['frame_queue'].get_nowait()
            except queue.Empty:
                break
        
        while not detection_state['violation_queue'].empty():
            try:
                detection_state['violation_queue'].get_nowait()
            except queue.Empty:
                break
        
        return Response({
            'status': 'success',
            'message': 'Session reset successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_models(request):
    """Get available YOLO models"""
    try:
        available_models = ['yolov8s', 'yolo11s', 'yolo12s']
        current_model = detection_state['current_settings']['model_name']
        
        return Response({
            'available_models': available_models,
            'current_model': current_model,
            'model_info': {
                'yolov8s': 'YOLOv8 Small - Fast and accurate',
                'yolo11s': 'YOLOv11 Small - Enhanced accuracy',
                'yolo12s': 'YOLOv12 Small - Latest model, best accuracy'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_model(request):
    """Switch YOLO model"""
    global detection_state
    
    try:
        model_name = request.data.get('model_name')
        
        if not model_name:
            return Response({
                'status': 'error',
                'message': 'Model name required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update settings
        detection_state['current_settings']['model_name'] = model_name
        
        # Clear current model to force reload
        detection_state['model'] = None
        
        return Response({
            'status': 'success',
            'message': f'Switched to {model_name} model',
            'current_model': model_name
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_session(request):
    """Export current session data"""
    try:
        session_data = {
            'session_info': {
                'model_name': detection_state['current_settings']['model_name'],
                'speed_limit': detection_state['current_settings']['speed_limit'],
                'video_path': detection_state['current_settings']['video_path'],
                'timestamp': datetime.now().isoformat()
            },
            'statistics': violation_stats,
            'settings': detection_state['current_settings']
        }
        
        return Response({
            'status': 'success',
            'session_data': session_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def guaranteed_speed_detection_worker():
    """Background worker for traffic violation detection - EXACT SAME AS ORIGINAL"""
    global detection_state, violation_stats
    
    try:
        video_path = detection_state['current_settings']['video_path']
        model = detection_state['model']
        speed_calc = detection_state['speed_calculator']
        
        if not os.path.exists(video_path):
            print(f"❌ Video not found: {video_path}")
            return
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Could not open video")
            return
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # PERFORMANCE OPTIMIZATIONS
        # 1. Frame skipping for faster processing
        frame_skip = max(1, int(fps // 8))  # Process ~8 FPS instead of full FPS
        
        # 2. Resolution scaling for faster inference
        target_size = 640  # YOLO optimal size
        scale_factor = min(target_size / frame_width, target_size / frame_height, 1.0)
        
        if scale_factor < 1.0:
            new_width = int(frame_width * scale_factor)
            new_height = int(frame_height * scale_factor)
            print(f"🔧 Scaling video from {frame_width}x{frame_height} to {new_width}x{new_height} for faster processing")
        else:
            new_width, new_height = frame_width, frame_height
        
        # Initialize speed calculator with video properties
        speed_calc.set_video_properties(fps, frame_width, frame_height)
        
        print(f"🎬 Video: {frame_width}x{frame_height} @ {fps:.1f} FPS ({total_frames} frames)")
        print(f"🚦 Speed limit: {detection_state['current_settings']['speed_limit']} km/h")
        print(f"⚡ OPTIMIZED processing: Skip {frame_skip} frames, Scale {scale_factor:.2f}x")
        print("🎯 Starting FAST & ACCURATE speed detection!")
        
        frame_count = 0
        processed_count = 0
        last_cleanup = time.time()
        
        while detection_state['is_detecting']:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
                frame_count = 0
                continue
            
            frame_count += 1
            
            # OPTIMIZATION: Skip frames for faster processing
            if frame_count % frame_skip != 0:
                continue
                
            processed_count += 1
            speed_calc.update_frame_count()
            current_time = time.time()
            
            # OPTIMIZATION: Resize frame for faster inference
            if scale_factor < 1.0:
                inference_frame = cv2.resize(frame, (new_width, new_height))
            else:
                inference_frame = frame
            
            # Run YOLO detection with optimized parameters
            results = model(inference_frame, conf=0.15, iou=0.4, verbose=False, imgsz=640)
            
            # Use original frame for display but scale detection coordinates back
            annotated_frame = frame.copy()
            frame_violations = []
            frame_counts = {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
            
            # Cleanup old tracks periodically (less frequent for performance)
            if current_time - last_cleanup > 15:  # Every 15 seconds instead of 10
                speed_calc.cleanup_old_tracks()
                last_cleanup = current_time
            
            # Process detections with coordinate scaling
            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # Get coordinates and scale back to original frame size
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        if scale_factor < 1.0:
                            x1 /= scale_factor
                            y1 /= scale_factor
                            x2 /= scale_factor
                            y2 /= scale_factor
                        conf = box.conf[0].cpu().numpy()
                        cls = int(box.cls[0].cpu().numpy())
                        
                        if conf > 0.15:  # Lowered threshold for better detection
                            class_name = model.names[cls]
                            
                            # Only process vehicles with optimized filtering
                            if class_name in ['car', 'truck', 'bus', 'motorcycle']:
                                # Quick filtering for performance
                                bbox_width = x2 - x1
                                bbox_height = y2 - y1
                                bbox_area = bbox_width * bbox_height
                                frame_area = frame_width * frame_height
                                
                                # Skip very small detections (optimized check)
                                if bbox_area < frame_area * 0.0003:  # Slightly lower threshold
                                    continue
                                
                                # Quick aspect ratio check
                                if bbox_height > 0:
                                    aspect_ratio = bbox_width / bbox_height
                                    if aspect_ratio < 0.2 or aspect_ratio > 5.0:  # Wider range for speed
                                        continue
                                
                                # Map vehicle types
                                type_map = {
                                    'car': ('cars', 'CAR'),
                                    'motorcycle': ('bikes', 'BIKE'),
                                    'bus': ('buses', 'BUS'),
                                    'truck': ('trucks', 'TRUCK')
                                }
                                
                                if class_name in type_map:
                                    vehicle_type, display_name = type_map[class_name]
                                    frame_counts[vehicle_type] += 1
                                    frame_counts['total'] += 1
                                    
                                    # OPTIMIZED vehicle ID generation
                                    center_x = int((x1 + x2) / 2)
                                    center_y = int((y1 + y2) / 2)
                                    # Larger grid for performance (less precise but faster)
                                    grid_x = center_x // 40
                                    grid_y = center_y // 40
                                    vehicle_id = f"{class_name}_{grid_x}_{grid_y}"
                                    
                                    # OPTIMIZED SPEED CALCULATION
                                    speed_kmh, status_method = speed_calc.calculate_guaranteed_speed(
                                        vehicle_id, [x1, y1, x2, y2], current_time
                                    )
                                    
                                    # HELMET DETECTION for motorcycles
                                    helmet_violation = None
                                    if class_name == 'motorcycle':
                                        try:
                                            helmet_detector = detection_state['helmet_detector']
                                            if helmet_detector:
                                                # Extract motorcycle region for analysis
                                                motorcycle_region = annotated_frame[int(y1):int(y2), int(x1):int(x2)]
                                                
                                                # Check if there's actually a person on the motorcycle
                                                person_detected = helmet_detector.detect_person_on_motorcycle(motorcycle_region)
                                                
                                                if person_detected:
                                                    helmet_result = helmet_detector.detect_helmet_multi_method(
                                                        annotated_frame, [x1, y1, x2, y2]
                                                    )
                                                    
                                                    print(f"🏍️ Motorcycle with rider - Helmet result: {helmet_result.get('has_helmet', False)}, Confidence: {helmet_result.get('confidence', 0):.2f}")
                                                    
                                                    # Check if no helmet detected
                                                    if not helmet_result.get('has_helmet', False):
                                                        helmet_violation = {
                                                            'type': 'NO_HELMET',
                                                            'timestamp': datetime.now().isoformat(),
                                                            'vehicle_type': 'motorcycle',
                                                            'confidence': helmet_result.get('confidence', 0.0),
                                                            'detection_method': helmet_result.get('method', 'multi_method'),
                                                            'bbox': [int(x1), int(y1), int(x2), int(y2)]
                                                        }
                                                        frame_violations.append(helmet_violation)
                                                        print(f"🚨 HELMET VIOLATION DETECTED! Confidence: {helmet_result.get('confidence', 0):.2f}")
                                                        
                                                        # Add helmet violation indicator to display
                                                        cv2.putText(annotated_frame, "NO HELMET!", 
                                                                   (int(x1), int(y2)+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                                    else:
                                                        # Show helmet detected
                                                        cv2.putText(annotated_frame, "HELMET OK", 
                                                                   (int(x1), int(y2)+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                                else:
                                                    # No person detected on motorcycle - don't check for helmet
                                                    print(f"🏍️ Empty motorcycle detected - skipping helmet check")
                                                    cv2.putText(annotated_frame, "EMPTY BIKE", 
                                                               (int(x1), int(y2)+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
                                        except Exception as e:
                                            print(f"⚠️ Helmet detection error: {e}")
                                            import traceback
                                            traceback.print_exc()
                                    
                                    # SPEED DISPLAY with performance optimizations
                                    speed_limit = detection_state['current_settings']['speed_limit']
                                    if speed_kmh == 0:
                                        color = (128, 128, 128)  # Gray for stationary
                                        speed_text = "0 km/h"
                                        status_text = "STATIONARY"
                                    elif speed_kmh > speed_limit:
                                        color = (0, 0, 255)  # Red for speeding
                                        speed_text = f"{speed_kmh:.0f} km/h FAST!"  # Simplified text
                                        status_text = "SPEEDING"
                                        
                                        # Create violation (less detailed for performance)
                                        violation = {
                                            'type': 'OVERSPEEDING',
                                            'timestamp': datetime.now().isoformat(),
                                            'vehicle_type': class_name,
                                            'speed': round(speed_kmh, 1),
                                            'speed_limit': speed_limit,
                                            'excess_speed': round(speed_kmh - speed_limit, 1),
                                            'confidence': float(conf)
                                        }
                                        frame_violations.append(violation)
                                    else:
                                        color = (0, 255, 0)  # Green for normal
                                        speed_text = f"{speed_kmh:.0f} km/h"  # Simplified
                                        status_text = "NORMAL"
                                    
                                    # OPTIMIZED drawing (fewer text overlays)
                                    thickness = 3 if speed_kmh > speed_limit else 2
                                    cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
                                    
                                    # Only essential text for performance
                                    cv2.putText(annotated_frame, f"{display_name}", 
                                               (int(x1), int(y1)-40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                                    
                                    # LARGE SPEED DISPLAY
                                    cv2.putText(annotated_frame, speed_text, 
                                               (int(x1), int(y1)-15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Update statistics less frequently for performance
            for vtype, count in frame_counts.items():
                violation_stats['vehicle_counts'][vtype] += count
            
            # Handle violations
            if frame_violations:
                violation_stats['total_violations'] += len(frame_violations)
                for violation in frame_violations:
                    if violation['type'] == 'OVERSPEEDING':
                        violation_stats['speed_violations'] += 1
                    elif violation['type'] == 'NO_HELMET':
                        violation_stats['helmet_violations'] += 1
                    
                    violation_stats['recent_violations'].append(violation)
                    if len(violation_stats['recent_violations']) > 5:  # Smaller history for performance
                        violation_stats['recent_violations'].pop(0)
                    
                    try:
                        detection_state['violation_queue'].put_nowait(violation)
                    except queue.Full:
                        pass
            
            # SIMPLIFIED info overlay for performance
            overlay_height = 80  # Smaller overlay
            cv2.rectangle(annotated_frame, (10, 10), (600, overlay_height), (0, 0, 0), -1)
            cv2.rectangle(annotated_frame, (10, 10), (600, overlay_height), (255, 255, 255), 2)
            
            # Essential info only
            cv2.putText(annotated_frame, "FAST TRAFFIC DETECTION", (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.putText(annotated_frame, f"Speed Limit: {detection_state['current_settings']['speed_limit']} km/h | Processed: {processed_count}", 
                       (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Progress indicator
            progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
            cv2.putText(annotated_frame, f"Progress: {progress:.1f}% | Processing: ~{8:.0f} FPS", 
                       (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Send frame to frontend (less frequently for performance)
            if processed_count % 2 == 0:  # Send every 2nd processed frame
                try:
                    # Encode frame with lower quality for speed
                    _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    frame_data = {
                        'image': f'data:image/jpeg;base64,{frame_base64}',  # Add proper data URL prefix
                        'stats': {
                            'frame_count': processed_count,
                            'progress': progress,
                            'vehicles_detected': frame_counts['total'],
                            'total_violations': violation_stats['total_violations'],
                            'speed_violations': violation_stats['speed_violations'],
                            'helmet_violations': violation_stats['helmet_violations'],  # MISSING - Added this!
                            'vehicle_counts': violation_stats['vehicle_counts']
                        }
                    }
                    
                    # Non-blocking queue put
                    try:
                        if detection_state['frame_queue'].full():
                            detection_state['frame_queue'].get_nowait()  # Remove old frame
                        detection_state['frame_queue'].put_nowait(frame_data)
                    except queue.Full:
                        pass  # Skip frame if queue is full
                        
                except Exception as e:
                    print(f"⚠️ Frame encoding error: {e}")
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.02)  # 20ms delay for stability
        
        cap.release()
        print("🛑 Traffic violation detection stopped")
        
    except Exception as e:
        print(f"❌ Detection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        detection_state['is_detecting'] = False