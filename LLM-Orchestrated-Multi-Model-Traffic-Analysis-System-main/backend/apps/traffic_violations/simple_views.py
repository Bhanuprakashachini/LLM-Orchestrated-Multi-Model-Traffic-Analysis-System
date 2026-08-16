"""
Simple Traffic Violations Views for Testing
"""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import os
from datetime import datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_videos(request):
    """Get available video files - includes uploaded videos"""
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
        
        # Check current directory for videos
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_models(request):
    """Get available YOLO models - simple version"""
    try:
        available_models = ['yolov8s', 'yolo11s', 'yolo12s']
        current_model = 'yolov8s'
        
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
def upload_video(request):
    """Handle video file upload - fully functional version"""
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
        
        # Basic validation
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
        from datetime import datetime
        
        # Create upload directory if it doesn't exist
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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def handle_settings(request):
    """Handle detection settings - simple version"""
    default_settings = {
        'speed_limit': 50,
        'model_name': 'yolov8s',
        'confidence_threshold': 0.25,
        'video_path': ''
    }
    
    if request.method == 'POST':
        try:
            # For now, just return the updated settings
            # TODO: Implement actual settings storage
            return Response({
                'status': 'success',
                'settings': default_settings,
                'message': 'Settings updated (mock implementation)'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(default_settings, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_detection(request):
    """Start detection - simple version"""
    return Response({
        'status': 'error',
        'message': 'Detection not yet implemented - this is a test endpoint'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_detection(request):
    """Stop detection - simple version"""
    return Response({
        'status': 'success',
        'message': 'Detection stopped (mock implementation)'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_frame(request):
    """Get current frame - simple version"""
    return Response({
        'image': None,
        'stats': {},
        'message': 'No active detection session'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_violations(request):
    """Get violations - simple version"""
    return Response({
        'violations': [],
        'stats': {
            'total_violations': 0,
            'speed_violations': 0,
            'helmet_violations': 0,
            'vehicle_counts': {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_statistics(request):
    """Get statistics - simple version"""
    return Response({
        'total_violations': 0,
        'speed_violations': 0,
        'helmet_violations': 0,
        'vehicle_counts': {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_session(request):
    """Reset session - simple version"""
    return Response({
        'status': 'success',
        'message': 'Session reset (mock implementation)'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_model(request):
    """Switch model - simple version"""
    return Response({
        'status': 'success',
        'message': 'Model switched (mock implementation)',
        'current_model': 'yolov8s'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_session(request):
    """Export session - simple version"""
    return Response({
        'status': 'error',
        'message': 'No active session to export'
    }, status=status.HTTP_400_BAD_REQUEST)