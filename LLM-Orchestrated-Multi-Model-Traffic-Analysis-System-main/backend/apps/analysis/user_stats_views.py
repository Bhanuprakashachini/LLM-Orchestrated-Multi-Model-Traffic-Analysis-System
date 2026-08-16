"""
User-specific analysis statistics and history views - MongoDB compatible
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .mongo_analysis import MongoAnalysisService
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]
users = db.users
user_stats = db.user_stats

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_dashboard_stats(request):
    """Get comprehensive user dashboard statistics"""
    try:
        user = request.user
        user_id = str(user.id)
        
        # Get or create user stats from MongoDB
        user_stats_doc = user_stats.find_one({'user_id': user_id})
        if not user_stats_doc:
            # Create default user stats
            user_stats_doc = {
                'user_id': user_id,
                'total_analyses': 0,
                'successful_analyses': 0,
                'failed_analyses': 0,
                'success_rate': 0.0,
                'total_vehicles_detected': 0,
                'total_processing_time': 0.0,
                'average_processing_time': 0.0,
                'average_vehicles_per_analysis': 0.0,
                'last_analysis_date': None,
                'recent_analysis_id': None,
                'recent_analysis_type': None,
                'recent_analysis_model': None,
                'last_activity_date': datetime.utcnow(),
                'favorite_analysis_type': 'image',
                'favorite_model': 'yolov8s',
                'most_active_hour': 12,
                'model_usage_stats': {},
                'analysis_type_stats': {},
                'current_streak_days': 0,
                'longest_streak_days': 0,
                'account_age_days': (datetime.utcnow() - user.date_joined).days if user.date_joined else 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            user_stats.insert_one(user_stats_doc)
        
        # Get MongoDB analysis service
        mongo_service = MongoAnalysisService()
        
        # Get MongoDB aggregated stats
        mongo_stats = mongo_service.get_user_analysis_stats(user_id)
        
        # Get model usage statistics
        model_usage = mongo_service.get_user_model_usage_stats(user_id)
        
        # Prepare dashboard data
        dashboard_data = {
            'user_info': {
                'id': user_id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.isoformat() if user.date_joined else datetime.utcnow().isoformat(),
                'account_age_days': user_stats_doc.get('account_age_days', 0)
            },
            'analysis_statistics': {
                'total_analyses': user_stats_doc.get('total_analyses', 0),
                'successful_analyses': user_stats_doc.get('successful_analyses', 0),
                'failed_analyses': user_stats_doc.get('failed_analyses', 0),
                'success_rate': user_stats_doc.get('success_rate', 0.0),
                'total_vehicles_detected': user_stats_doc.get('total_vehicles_detected', 0),
                'total_processing_time': user_stats_doc.get('total_processing_time', 0.0),
                'average_processing_time': user_stats_doc.get('average_processing_time', 0.0),
                'average_vehicles_per_analysis': user_stats_doc.get('average_vehicles_per_analysis', 0.0)
            },
            'recent_activity': {
                'last_analysis_date': user_stats_doc.get('last_analysis_date').isoformat() if user_stats_doc.get('last_analysis_date') else None,
                'recent_analysis_id': user_stats_doc.get('recent_analysis_id'),
                'recent_analysis_type': user_stats_doc.get('recent_analysis_type'),
                'recent_analysis_model': user_stats_doc.get('recent_analysis_model'),
                'last_activity_date': user_stats_doc.get('last_activity_date').isoformat() if user_stats_doc.get('last_activity_date') else None
            },
            'usage_patterns': {
                'favorite_analysis_type': user_stats_doc.get('favorite_analysis_type', 'image'),
                'favorite_model': user_stats_doc.get('favorite_model', 'yolov8s'),
                'most_active_hour': user_stats_doc.get('most_active_hour', 12),
                'model_usage_stats': user_stats_doc.get('model_usage_stats', {}),
                'analysis_type_stats': user_stats_doc.get('analysis_type_stats', {})
            },
            'engagement_metrics': {
                'current_streak_days': user_stats_doc.get('current_streak_days', 0),
                'longest_streak_days': user_stats_doc.get('longest_streak_days', 0)
            },
            'model_performance': model_usage,
            'mongodb_stats': mongo_stats
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting user dashboard stats for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to retrieve user statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_analysis_history(request):
    """Get user's analysis history with pagination"""
    try:
        user = request.user
        user_id = str(user.id)
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        analysis_type = request.GET.get('type', None)
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Get MongoDB analysis service
        mongo_service = MongoAnalysisService()
        
        # Get user analyses
        result = mongo_service.get_user_analyses(
            user_id=user_id,
            limit=limit,
            skip=skip,
            analysis_type=analysis_type
        )
        
        # Prepare response
        response_data = {
            'analyses': result['analyses'],
            'pagination': {
                'current_page': page,
                'total_count': result['total_count'],
                'has_more': result['has_more'],
                'per_page': limit,
                'total_pages': (result['total_count'] + limit - 1) // limit
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting user analysis history for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to retrieve analysis history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_analysis_trends(request):
    """Get user's analysis trends over time"""
    try:
        user = request.user
        user_id = str(user.id)
        
        # Get time period from query params
        days = int(request.GET.get('days', 30))
        
        # Get MongoDB analysis service
        mongo_service = MongoAnalysisService()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get trend data from MongoDB
        pipeline = [
            {
                '$match': {
                    'user_id': user_id,
                    'created_at': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$created_at'},
                        'month': {'$month': '$created_at'},
                        'day': {'$dayOfMonth': '$created_at'}
                    },
                    'count': {'$sum': 1},
                    'successful': {'$sum': {'$cond': [{'$eq': ['$success', True]}, 1, 0]}},
                    'total_vehicles': {'$sum': '$vehicle_detection.total_vehicles'},
                    'avg_processing_time': {'$avg': '$processing_time'}
                }
            },
            {
                '$sort': {'_id.year': 1, '_id.month': 1, '_id.day': 1}
            }
        ]
        
        results = list(mongo_service.analyses.aggregate(pipeline))
        
        # Format trend data
        trend_data = []
        for result in results:
            date_obj = datetime(
                result['_id']['year'],
                result['_id']['month'],
                result['_id']['day']
            )
            
            trend_data.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'analyses_count': result['count'],
                'successful_count': result['successful'],
                'success_rate': (result['successful'] / result['count'] * 100) if result['count'] > 0 else 0,
                'total_vehicles': result['total_vehicles'],
                'avg_processing_time': result['avg_processing_time']
            })
        
        return Response({
            'period_days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'trend_data': trend_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user analysis trends for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to retrieve analysis trends'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_analysis_to_db(request):
    """Save analysis data to MongoDB with user tracking"""
    logger.info(f"🔥 SAVE REQUEST RECEIVED from user: {request.user.username if request.user else 'Unknown'}")
    logger.info(f"🔥 Request method: {request.method}")
    logger.info(f"🔥 Request headers: {dict(request.headers)}")
    logger.info(f"🔥 Request data keys: {list(request.data.keys()) if request.data else 'No data'}")
    
    try:
        user = request.user
        user_id = str(user.id)
        analysis_data = request.data.get('analysis_data', {})
        
        logger.info(f"📥 Save request from user {user_id}: {user.username}")
        logger.info(f"📊 Analysis data keys: {list(analysis_data.keys()) if analysis_data else 'No data'}")
        
        if not analysis_data:
            logger.warning(f"❌ No analysis data provided by user {user_id}")
            return Response({
                'error': 'No analysis data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get MongoDB analysis service
        try:
            mongo_service = MongoAnalysisService()
            logger.info(f"✅ MongoDB service initialized for user {user_id}")
        except Exception as mongo_error:
            logger.error(f"❌ MongoDB service initialization failed: {mongo_error}")
            return Response({
                'error': 'Database connection failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Prepare analysis data for storage
        storage_data = {
            'analysis_type': request.data.get('analysis_type', 'comprehensive_comparison'),
            'model_version': 'Multi-Model Comparison',
            'processing_time': analysis_data.get('comparison_summary', {}).get('analysis_time', 0),
            'vehicle_detection': {
                'total_vehicles': analysis_data.get('vehicle_detection_summary', {}).get('total_vehicles', 0),
                'detection_summary': analysis_data.get('vehicle_detection_summary', {}).get('vehicle_counts', {}),
                'best_model': analysis_data.get('vehicle_detection_summary', {}).get('best_model_used', 'unknown')
            },
            'comparison_results': analysis_data.get('comparison_table', []),
            'recommendations': analysis_data.get('recommendations', {}),
            'images': analysis_data.get('images', {}),  # Include image data
            'advanced_features': analysis_data.get('advanced_features', {}),
            'success': True,
            'status': 'completed'
        }
        
        # Create analysis in MongoDB
        logger.info(f"💾 Attempting to save analysis for user {user_id}")
        analysis_id = mongo_service.create_analysis(user_id, storage_data)
        
        if analysis_id:
            logger.info(f"✅ Analysis saved successfully with ID: {analysis_id}")
            return Response({
                'success': True,
                'analysis_id': analysis_id,
                'message': 'Analysis saved successfully'
            })
        else:
            logger.error(f"❌ Failed to create analysis in MongoDB for user {user_id}")
            return Response({
                'error': 'Failed to save analysis'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error saving analysis for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to save analysis to database'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)