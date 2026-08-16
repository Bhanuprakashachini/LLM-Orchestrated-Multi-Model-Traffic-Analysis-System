"""
Traffic Violations Detection Views
Django REST API endpoints for traffic violation detection system
"""

import os
import cv2
import json
import base64
import threading
import time
import queue
from datetime import datetime
from typing import Dict, Optional

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services.violation_detector import ViolationDetector
from .utils.file_storage import file_storage


# Global variables for detection state
detection_state = {
    'is_detecting': False,
    'detection_thread': None,
    'violation_detector': None,
    'current_settings': {
        'speed_limit': 50,
        'model_name': 'yolov8s',
        'confidence_threshold': 0.25,
        'video_path': '',
        'video_source_type': 'file'
    },
    'frame_queue': queue.Queue(maxsize=1),
    'violation_queue': queue.Queue(maxsize=10)
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
        
        # Save file using file storage
        file_path = file_storage.save_uploaded_video(uploaded_file, uploaded_file.name)
        file_size = uploaded_file.size / (1024 * 1024)  # MB
        
        return Response({
            'status': 'success',
            'message': f'Video uploaded successfully: {uploaded_file.name}',
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
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
        videos = file_storage.list_uploaded_videos()
        
        # Also check for videos in current directory and common locations
        additional_videos = []
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')
        
        # Check current directory
        try:
            for file in os.listdir('.'):
                if file.lower().endswith(video_extensions):
                    file_size = os.path.getsize(file) / (1024 * 1024)
                    additional_videos.append({
                        'name': file,
                        'path': file,
                        'size': f"{file_size:.1f} MB",
                        'location': 'Current Directory',
                        'created_at': datetime.fromtimestamp(os.path.getctime(file)).isoformat()
                    })
        except Exception:
            pass
        
        # Check Traffic detection system folder
        traffic_dir = 'Traffic detection system'
        if os.path.exists(traffic_dir):
            try:
                for file in os.listdir(traffic_dir):
                    if file.lower().endswith(video_extensions):
                        full_path = os.path.join(traffic_dir, file)
                        file_size = os.path.getsize(full_path) / (1024 * 1024)
                        additional_videos.append({
                            'name': file,
                            'path': full_path,
                            'size': f"{file_size:.1f} MB",
                            'location': 'Traffic Detection System',
                            'created_at': datetime.fromtimestamp(os.path.getctime(full_path)).isoformat()
                        })
            except Exception:
                pass
        
        # Combine and sort videos
        all_videos = videos + additional_videos
        all_videos.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return Response({
            'videos': all_videos,
            'count': len(all_videos),
            'message': f"Found {len(all_videos)} video files" if all_videos else "No video files found"
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
    """Start traffic violation detection"""
    global detection_state
    
    try:
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
        
        # Initialize violation detector
        settings = detection_state['current_settings']
        detection_state['violation_detector'] = ViolationDetector(
            model_name=settings['model_name'],
            speed_limit=settings['speed_limit']
        )
        detection_state['violation_detector'].set_confidence_threshold(settings['confidence_threshold'])
        
        # Start detection thread
        detection_state['is_detecting'] = True
        detection_state['detection_thread'] = threading.Thread(
            target=detection_worker,
            daemon=True
        )
        detection_state['detection_thread'].start()
        
        return Response({
            'status': 'success',
            'message': f'Traffic violation detection started with {settings["model_name"]} model',
            'settings': settings
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
            return Response(frame_data, status=status.HTTP_200_OK)
        else:
            # Return empty response if no frame available
            return Response({
                'image': None,
                'stats': detection_state['violation_detector'].get_session_statistics() 
                        if detection_state['violation_detector'] else {}
            }, status=status.HTTP_200_OK)
    except Exception as e:
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
        
        # Get session statistics
        stats = {}
        if detection_state['violation_detector']:
            stats = detection_state['violation_detector'].get_session_statistics()
        
        return Response({
            'violations': violations,
            'stats': stats
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
        if detection_state['violation_detector']:
            stats = detection_state['violation_detector'].get_session_statistics()
        else:
            stats = {
                'total_violations': 0,
                'speed_violations': 0,
                'helmet_violations': 0,
                'vehicle_counts': {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
            }
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_session(request):
    """Reset current detection session"""
    try:
        if detection_state['violation_detector']:
            detection_state['violation_detector'].reset_session()
        
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
        from .services.yolo_processor import YOLOProcessor
        
        available_models = list(YOLOProcessor.AVAILABLE_MODELS.keys())
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
    try:
        model_name = request.data.get('model_name')
        
        if not model_name:
            return Response({
                'status': 'error',
                'message': 'Model name required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update settings
        detection_state['current_settings']['model_name'] = model_name
        
        # Update detector if running
        if detection_state['violation_detector']:
            detection_state['violation_detector'].switch_model(model_name)
        
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
        if detection_state['violation_detector']:
            session_data = detection_state['violation_detector'].export_session_data()
            
            # Save to file storage
            session_id = file_storage.save_session({
                'user_id': str(request.user.id) if hasattr(request.user, 'id') else 'anonymous',
                'session_data': session_data,
                'settings': detection_state['current_settings']
            })
            
            return Response({
                'status': 'success',
                'session_id': session_id,
                'session_data': session_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'No active session to export'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def detection_worker():
    """Background worker for traffic violation detection"""
    global detection_state
    
    try:
        video_path = detection_state['current_settings']['video_path']
        violation_detector = detection_state['violation_detector']
        
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
        
        print(f"🎬 Video: {frame_width}x{frame_height} @ {fps:.1f} FPS")
        print(f"🚦 Speed limit: {detection_state['current_settings']['speed_limit']} km/h")
        print(f"🤖 Model: {detection_state['current_settings']['model_name']}")
        print("🎯 Starting traffic violation detection...")
        
        frame_count = 0
        
        while detection_state['is_detecting']:
            ret, frame = cap.read()
            if not ret:
                # Loop video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            frame_count += 1
            
            # Process frame for violations
            result = violation_detector.process_frame(frame)
            
            # Convert frame to base64 for transmission
            _, buffer = cv2.imencode('.jpg', result['annotated_frame'], 
                                   [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare frame data
            frame_data = {
                'image': frame_base64,
                'stats': {
                    'frame_count': result['frame_number'],
                    'vehicles_detected': result['vehicle_counts']['total'],
                    'processing_time': result['processing_time'],
                    'timestamp': result['timestamp']
                },
                'detections': result['detections'],
                'vehicle_counts': result['vehicle_counts']
            }
            
            # Update frame queue
            try:
                if detection_state['frame_queue'].full():
                    detection_state['frame_queue'].get_nowait()
                detection_state['frame_queue'].put_nowait(frame_data)
            except queue.Full:
                pass
            
            # Add violations to queue
            for violation in result['violations']:
                try:
                    # Save violation to file storage
                    file_storage.save_violation(violation)
                    
                    # Add to queue for real-time updates
                    if not detection_state['violation_queue'].full():
                        detection_state['violation_queue'].put_nowait(violation)
                except queue.Full:
                    pass
            
            # Control frame rate (20 FPS for smooth display)
            time.sleep(1.0 / 20)
        
        cap.release()
        print("🛑 Traffic violation detection stopped")
        
    except Exception as e:
        print(f"❌ Detection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        detection_state['is_detecting'] = False