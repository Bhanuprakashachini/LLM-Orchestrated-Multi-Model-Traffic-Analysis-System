"""
User management views - MongoDB compatible
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .serializers import (
    UserPreferencesSerializer, UserActivitySerializer, UserStatsSerializer,
    UserQuotaSerializer, UserProfileExtendedSerializer, TeamMemberSerializer
)
from ..authentication.mongo_auth import mongo_auth
from utils.mongodb import get_mongo_collection

logger = logging.getLogger(__name__)


class UserManagementViewSet(viewsets.ViewSet):
    """
    ViewSet for user management operations - MongoDB compatible
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get user profile",
        description="Get extended user profile with preferences and stats"
    )
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get user profile"""
        try:
            user_id = str(request.user.id)
            db = get_mongo_client()
            
            # Get or create user stats in MongoDB
            user_stats = db.user_stats.find_one({'user_id': user_id})
            if not user_stats:
                user_stats = {
                    'user_id': user_id,
                    'total_analyses': 0,
                    'total_processing_time': 0.0,
                    'total_vehicles_detected': 0,
                    'favorite_analysis_type': 'image',
                    'current_streak_days': 0,
                    'longest_streak_days': 0,
                    'average_processing_time': 0.0,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                db.user_stats.insert_one(user_stats)
            
            # Get or create user quota in MongoDB
            user_quota = db.user_quotas.find_one({'user_id': user_id})
            if not user_quota:
                user_quota = {
                    'user_id': user_id,
                    'daily_analyses_limit': 100,
                    'monthly_analyses_limit': 1000,
                    'storage_limit_mb': 1000.0,
                    'api_calls_limit': 1000,
                    'daily_analyses_used': 0,
                    'monthly_analyses_used': 0,
                    'storage_used_mb': 0.0,
                    'api_calls_used': 0,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                db.user_quotas.insert_one(user_quota)
            
            # Get user preferences
            user_preferences = db.user_preferences.find_one({'user_id': user_id})
            if not user_preferences:
                user_preferences = {
                    'user_id': user_id,
                    'theme': 'light',
                    'language': 'en',
                    'notifications_enabled': True,
                    'email_notifications': True,
                    'auto_save_analyses': True,
                    'default_analysis_type': 'image',
                    'dashboard_layout': {},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                db.user_preferences.insert_one(user_preferences)
            
            return Response({
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name
                },
                'stats': {
                    'total_analyses': user_stats.get('total_analyses', 0),
                    'total_processing_time': user_stats.get('total_processing_time', 0.0),
                    'total_vehicles_detected': user_stats.get('total_vehicles_detected', 0),
                    'favorite_analysis_type': user_stats.get('favorite_analysis_type', 'image'),
                    'current_streak_days': user_stats.get('current_streak_days', 0),
                    'longest_streak_days': user_stats.get('longest_streak_days', 0),
                    'average_processing_time': user_stats.get('average_processing_time', 0.0)
                },
                'quota': {
                    'daily_analyses_limit': user_quota.get('daily_analyses_limit', 100),
                    'monthly_analyses_limit': user_quota.get('monthly_analyses_limit', 1000),
                    'storage_limit_mb': user_quota.get('storage_limit_mb', 1000.0),
                    'daily_analyses_used': user_quota.get('daily_analyses_used', 0),
                    'monthly_analyses_used': user_quota.get('monthly_analyses_used', 0),
                    'storage_used_mb': user_quota.get('storage_used_mb', 0.0)
                },
                'preferences': {
                    'theme': user_preferences.get('theme', 'light'),
                    'language': user_preferences.get('language', 'en'),
                    'notifications_enabled': user_preferences.get('notifications_enabled', True),
                    'email_notifications': user_preferences.get('email_notifications', True),
                    'auto_save_analyses': user_preferences.get('auto_save_analyses', True),
                    'default_analysis_type': user_preferences.get('default_analysis_type', 'image'),
                    'dashboard_layout': user_preferences.get('dashboard_layout', {})
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return Response({
                'error': 'Failed to get user profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="Update user preferences",
        description="Update user preferences and settings"
    )
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update user preferences"""
        try:
            user_id = str(request.user.id)
            db = get_mongo_client()
            
            # Update preferences in MongoDB
            preferences_data = request.data
            preferences_data['user_id'] = user_id
            preferences_data['updated_at'] = datetime.utcnow()
            
            db.user_preferences.update_one(
                {'user_id': user_id},
                {'$set': preferences_data},
                upsert=True
            )
            
            # Log activity
            db.user_activities.insert_one({
                'user_id': user_id,
                'activity_type': 'settings_change',
                'description': 'Updated user preferences',
                'metadata': {'preferences': preferences_data},
                'timestamp': datetime.utcnow(),
                'ip_address': self._get_client_ip(request)
            })
            
            return Response({
                'message': 'Preferences updated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return Response({
                'error': 'Failed to update preferences'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="Get user activity",
        description="Get recent user activity history"
    )
    @action(detail=False, methods=['get'])
    def activity(self, request):
        """Get user activity"""
        try:
            user_id = str(request.user.id)
            db = get_mongo_client()
            
            # Get recent activities
            activities = list(db.user_activities.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(50))
            
            # Convert ObjectId to string for JSON serialization
            for activity in activities:
                activity['_id'] = str(activity['_id'])
                if 'timestamp' in activity:
                    activity['timestamp'] = activity['timestamp'].isoformat()
            
            return Response({
                'activities': activities
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return Response({
                'error': 'Failed to get user activity'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="Get user statistics",
        description="Get detailed user statistics and metrics"
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        try:
            user_id = str(request.user.id)
            db = get_mongo_client()
            
            # Get user stats
            user_stats = db.user_stats.find_one({'user_id': user_id})
            if not user_stats:
                user_stats = {
                    'total_analyses': 0,
                    'total_processing_time': 0.0,
                    'total_vehicles_detected': 0,
                    'favorite_analysis_type': 'image',
                    'current_streak_days': 0,
                    'longest_streak_days': 0,
                    'average_processing_time': 0.0
                }
            
            return Response({
                'stats': user_stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return Response({
                'error': 'Failed to get user statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get user notifications"""
    try:
        user_id = str(request.user.id)
        db = get_mongo_client()
        
        # Get unread notifications
        unread_notifications = list(db.user_notifications.find({
            'user_id': user_id,
            'is_read': False
        }).sort('created_at', -1))
        
        # Get recent read notifications
        read_notifications = list(db.user_notifications.find({
            'user_id': user_id,
            'is_read': True
        }).sort('created_at', -1).limit(10))
        
        # Convert ObjectId to string
        for notification in unread_notifications + read_notifications:
            notification['_id'] = str(notification['_id'])
            if 'created_at' in notification:
                notification['created_at'] = notification['created_at'].isoformat()
        
        return Response({
            'unread': unread_notifications,
            'read': read_notifications,
            'unread_count': len(unread_notifications)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return Response({
            'error': 'Failed to get notifications'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        user_id = str(request.user.id)
        db = get_mongo_client()
        
        # Update notification
        result = db.user_notifications.update_one(
            {'_id': notification_id, 'user_id': user_id},
            {'$set': {'is_read': True, 'read_at': datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return Response({
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'message': 'Notification marked as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return Response({
            'error': 'Failed to mark notification as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teams(request):
    """Get user teams"""
    try:
        user_id = str(request.user.id)
        db = get_mongo_client()
        
        # Get teams where user is a member
        teams = list(db.teams.find({
            'members': {'$elemMatch': {'user_id': user_id, 'is_active': True}},
            'is_active': True
        }))
        
        team_data = []
        for team in teams:
            # Find user's membership info
            membership = next((m for m in team['members'] if m['user_id'] == user_id), None)
            
            team_data.append({
                'id': str(team['_id']),
                'name': team['name'],
                'description': team.get('description', ''),
                'role': membership['role'] if membership else 'member',
                'member_count': len([m for m in team['members'] if m['is_active']]),
                'created_at': team['created_at'].isoformat() if 'created_at' in team else None
            })
        
        return Response({
            'teams': team_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        return Response({
            'error': 'Failed to get teams'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)