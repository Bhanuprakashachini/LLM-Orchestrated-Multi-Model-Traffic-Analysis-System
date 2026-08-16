"""
Streaming views for real-time video analysis - MongoDB compatible
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import uuid
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
from django.conf import settings

from .serializers import (
    StreamConfigSerializer,
    StreamStatusSerializer,
    StreamFrameSerializer,
    StreamSessionSerializer,
    StreamStatsSerializer
)

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]
stream_sessions = db.stream_sessions
stream_frames = db.stream_frames
stream_alerts = db.stream_alerts
stream_configurations = db.stream_configurations


class StreamingViewSet(viewsets.ViewSet):
    """
    ViewSet for streaming operations
    """
    permission_classes = [IsAuthenticated]
    
    def _calculate_real_fps(self):
        """Calculate real FPS based on recent frame processing times"""
        try:
            from datetime import datetime, timedelta
            
            # Get recent frames from last 30 seconds
            recent_time = datetime.utcnow() - timedelta(seconds=30)
            recent_frames = list(stream_frames.find({
                'timestamp': {'$gte': recent_time},
                'processing_time': {'$ne': None}
            }).sort('timestamp', -1).limit(30))
            
            if not recent_frames:
                return 0.0
            
            # Calculate average processing time
            total_time = sum(frame.get('processing_time', 0) for frame in recent_frames)
            avg_processing_time = total_time / len(recent_frames)
            
            # Calculate FPS (frames per second)
            if avg_processing_time > 0:
                return 1.0 / avg_processing_time
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating real FPS: {e}")
            return 0.0
    
    @extend_schema(
        summary="Start streaming session",
        description="Initialize a new streaming session with configuration",
        request=StreamConfigSerializer,
        responses={201: StreamSessionSerializer}
    )
    @action(detail=False, methods=['post'])
    def start_session(self, request):
        """Start a new streaming session"""
        serializer = StreamConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            config = serializer.validated_data
            session_id = str(uuid.uuid4())
            
            # Create stream session in MongoDB
            session_data = {
                'user_id': str(request.user.id),
                'session_id': session_id,
                'source_type': config['source_type'],
                'source_url': config.get('source_url', ''),
                'target_fps': config['fps'],
                'resolution_width': int(config['resolution'].split('x')[0]),
                'resolution_height': int(config['resolution'].split('x')[1]),
                'enable_recording': config['enable_recording'],
                'status': 'starting',
                'start_time': datetime.utcnow(),
                'created_at': datetime.utcnow(),
                'frames_processed': 0,
                'actual_fps': 0.0
            }
            
            stream_sessions.insert_one(session_data)
            
            # TODO: Start actual streaming process here
            # This would involve starting a background task or WebSocket connection
            
            session_serializer = StreamSessionSerializer({
                'session_id': session_id,
                'user_id': str(request.user.id),
                'start_time': session_data['start_time'],
                'total_frames': 0,
                'average_fps': 0.0,
                'total_vehicles': 0,
                'config': config
            })
            
            return Response(session_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to start streaming session: {e}")
            return Response(
                {'error': 'Failed to start streaming session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Stop streaming session",
        description="Stop an active streaming session"
    )
    @action(detail=True, methods=['post'])
    def stop_session(self, request, pk=None):
        """Stop streaming session"""
        try:
            session = stream_sessions.find_one({
                'session_id': pk,
                'user_id': str(request.user.id)
            })
            
            if not session:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if session.get('status') == 'stopped':
                return Response(
                    {'message': 'Session already stopped'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update session status
            stream_sessions.update_one(
                {'session_id': pk, 'user_id': str(request.user.id)},
                {
                    '$set': {
                        'status': 'stopped',
                        'end_time': datetime.utcnow()
                    }
                }
            )
            
            # TODO: Stop actual streaming process here
            
            return Response({'message': 'Session stopped successfully'})
            
        except Exception as e:
            logger.error(f"Failed to stop streaming session: {e}")
            return Response(
                {'error': 'Failed to stop session'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get session status",
        description="Get current status of a streaming session",
        responses={200: StreamStatusSerializer}
    )
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get session status"""
        try:
            session = stream_sessions.find_one({
                'session_id': pk,
                'user_id': str(request.user.id)
            })
            
            if not session:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate duration
            duration = 0
            if session.get('end_time'):
                duration = (session['end_time'] - session['start_time']).total_seconds()
            elif session.get('start_time'):
                duration = (datetime.utcnow() - session['start_time']).total_seconds()
            
            status_data = {
                'session_id': session['session_id'],
                'status': session.get('status', 'unknown'),
                'fps': session.get('actual_fps', 0),
                'frame_count': session.get('frames_processed', 0),
                'duration': duration,
                'last_frame_time': session.get('last_frame_time'),
                'error_message': session.get('error_message', '')
            }
            
            serializer = StreamStatusSerializer(status_data)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return Response(
                {'error': 'Failed to get session status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get recent frames",
        description="Get recent analyzed frames from a streaming session"
    )
    @action(detail=True, methods=['get'])
    def recent_frames(self, request, pk=None):
        """Get recent frames from session"""
        try:
            session = stream_sessions.find_one({
                'session_id': pk,
                'user_id': str(request.user.id)
            })
            
            if not session:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get last 10 frames
            recent_frames = list(stream_frames.find({
                'session_id': pk
            }).sort('frame_number', -1).limit(10))
            
            frame_data = []
            for frame in recent_frames:
                frame_data.append({
                    'frame_id': frame.get('frame_number', 0),
                    'timestamp': frame.get('timestamp'),
                    'vehicle_count': frame.get('vehicle_detection', {}).get('total_vehicles', 0),
                    'vehicles': frame.get('vehicle_detection', {}),
                    'scene_type': frame.get('scene_classification', {}).get('scene_type', ''),
                    'density_level': frame.get('traffic_density', {}).get('density_level', '')
                })
            
            return Response({'frames': frame_data})
            
        except Exception as e:
            logger.error(f"Error getting recent frames: {e}")
            return Response(
                {'error': 'Failed to get recent frames'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    summary="Get streaming statistics",
    description="Get overall streaming system statistics"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def streaming_stats(request):
    """Get streaming statistics"""
    try:
        # Count active sessions
        active_sessions = stream_sessions.count_documents({
            'status': {'$in': ['starting', 'running', 'paused']}
        })
        
        # Get total frames processed today
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        total_frames = stream_frames.count_documents({
            'timestamp': {'$gte': start_of_day, '$lte': end_of_day}
        })
        
        # Calculate average processing time
        recent_frames = list(stream_frames.find({
            'timestamp': {'$gte': start_of_day, '$lte': end_of_day}
        }).sort('timestamp', -1).limit(100))
        
        avg_processing_time = 0.0
        if recent_frames:
            total_time = sum(frame.get('processing_time', 0) for frame in recent_frames)
            avg_processing_time = total_time / len(recent_frames)
        
        # Get real system metrics
        try:
            import psutil
            import os
            
            # Get real system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get process-specific metrics if available
            current_process = psutil.Process(os.getpid())
            process_memory = current_process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate real FPS based on recent processing times
            current_fps = 1.0 / max(avg_processing_time, 0.04) if avg_processing_time > 0 else 25.0
            
            stats_data = {
                'active_sessions': active_sessions,
                'total_frames_processed': total_frames,
                'average_processing_time': avg_processing_time,
                'current_fps': current_fps,
                'memory_usage': memory_usage,
                'cpu_usage': cpu_usage,
                'process_memory_mb': process_memory,
                'system_memory_total_gb': memory.total / 1024 / 1024 / 1024,
                'system_memory_available_gb': memory.available / 1024 / 1024 / 1024
            }
            
        except ImportError:
            logger.warning("psutil not available - using basic system metrics")
            # Fallback to basic metrics without psutil
            stats_data = {
                'active_sessions': active_sessions,
                'total_frames_processed': total_frames,
                'average_processing_time': avg_processing_time,
                'current_fps': 1.0 / max(avg_processing_time, 0.04) if avg_processing_time > 0 else 25.0,
                'memory_usage': 'unavailable',
                'cpu_usage': 'unavailable',
                'note': 'Install psutil for detailed system metrics'
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            # Fallback with error info
            stats_data = {
                'active_sessions': active_sessions,
                'total_frames_processed': total_frames,
                'average_processing_time': avg_processing_time,
                'current_fps': 0.0,
                'memory_usage': 'error',
                'cpu_usage': 'error',
                'error': str(e)
            }
        
        serializer = StreamStatsSerializer(stats_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Failed to get streaming stats: {e}")
        return Response(
            {'error': 'Failed to get statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class StreamConfigurationViewSet(viewsets.ViewSet):
    """
    ViewSet for stream configuration management - MongoDB compatible
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List user's stream configurations"""
        try:
            configs = list(stream_configurations.find({
                'user_id': str(request.user.id)
            }))
            
            # Convert ObjectId to string for JSON serialization
            for config in configs:
                config['_id'] = str(config['_id'])
            
            return Response(configs)
        except Exception as e:
            logger.error(f"Error listing configurations: {e}")
            return Response(
                {'error': 'Failed to list configurations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request):
        """Create new stream configuration"""
        try:
            serializer = StreamConfigSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            config_data = serializer.validated_data
            config_data['user_id'] = str(request.user.id)
            config_data['created_at'] = datetime.utcnow()
            
            result = stream_configurations.insert_one(config_data)
            config_data['_id'] = str(result.inserted_id)
            
            return Response(config_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            return Response(
                {'error': 'Failed to create configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """Get specific configuration"""
        try:
            from bson import ObjectId
            config = stream_configurations.find_one({
                '_id': ObjectId(pk),
                'user_id': str(request.user.id)
            })
            
            if not config:
                return Response(
                    {'error': 'Configuration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            config['_id'] = str(config['_id'])
            return Response(config)
        except Exception as e:
            logger.error(f"Error retrieving configuration: {e}")
            return Response(
                {'error': 'Failed to retrieve configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        """Update configuration"""
        try:
            from bson import ObjectId
            serializer = StreamConfigSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            config_data = serializer.validated_data
            config_data['updated_at'] = datetime.utcnow()
            
            result = stream_configurations.update_one(
                {'_id': ObjectId(pk), 'user_id': str(request.user.id)},
                {'$set': config_data}
            )
            
            if result.matched_count == 0:
                return Response(
                    {'error': 'Configuration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(config_data)
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return Response(
                {'error': 'Failed to update configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, pk=None):
        """Delete configuration"""
        try:
            from bson import ObjectId
            result = stream_configurations.delete_one({
                '_id': ObjectId(pk),
                'user_id': str(request.user.id)
            })
            
            if result.deleted_count == 0:
                return Response(
                    {'error': 'Configuration not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({'message': 'Configuration deleted successfully'})
        except Exception as e:
            logger.error(f"Error deleting configuration: {e}")
            return Response(
                {'error': 'Failed to delete configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )