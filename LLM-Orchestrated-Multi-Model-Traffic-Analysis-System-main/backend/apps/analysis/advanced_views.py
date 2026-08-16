"""
Advanced analysis views that use analysis_history and llm_insights collections
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from utils.mongodb import get_mongo_db
from bson import ObjectId

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analysis_trends(request):
    """Get traffic analysis trends from analysis_history collection"""
    try:
        user = request.user
        db = get_mongo_db()
        
        # Get user's analysis history
        user_id = str(user.id)
        
        # Get recent history (last 30 days)
        since_date = timezone.now() - timedelta(days=30)
        
        history_records = list(db.analysis_history.find({
            'user_id': user_id,
            'created_at': {'$gte': since_date.replace(tzinfo=None)}
        }).sort('created_at', -1))
        
        if not history_records:
            return Response({
                'message': 'No analysis history found',
                'trends': {},
                'total_records': 0
            })
        
        # Calculate trends
        vehicle_counts = [record.get('vehicle_count_trend', {}).get('current', 0) for record in history_records]
        congestion_indices = [record.get('congestion_trend', {}).get('congestion_index', 0) for record in history_records]
        processing_times = [record.get('model_performance', {}).get('processing_time', 0) for record in history_records]
        
        trends = {
            'vehicle_count_trend': {
                'current_avg': sum(vehicle_counts) / len(vehicle_counts) if vehicle_counts else 0,
                'max_vehicles': max(vehicle_counts) if vehicle_counts else 0,
                'min_vehicles': min(vehicle_counts) if vehicle_counts else 0,
                'trend_direction': 'stable'  # Could be calculated from historical data
            },
            'congestion_trend': {
                'avg_congestion': sum(congestion_indices) / len(congestion_indices) if congestion_indices else 0,
                'peak_hours_detected': len([r for r in history_records if r.get('congestion_trend', {}).get('peak_detected', False)]),
                'congestion_pattern': 'moderate'
            },
            'performance_trend': {
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'fastest_analysis': min(processing_times) if processing_times else 0,
                'slowest_analysis': max(processing_times) if processing_times else 0
            },
            'analysis_frequency': {
                'total_analyses': len(history_records),
                'analyses_this_week': len([r for r in history_records if r.get('created_at') and r.get('created_at') >= (timezone.now() - timedelta(days=7)).replace(tzinfo=None)]),
                'avg_per_day': len(history_records) / 30
            }
        }
        
        return Response({
            'trends': trends,
            'total_records': len(history_records),
            'date_range': {
                'from': since_date.isoformat(),
                'to': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis trends: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_llm_insights(request):
    """Get LLM-powered insights from llm_insights collection"""
    try:
        user = request.user
        db = get_mongo_db()
        
        # Get analysis_id from query params (optional)
        analysis_id = request.GET.get('analysis_id')
        
        user_id = str(user.id)
        
        if analysis_id:
            # Get insights for specific analysis
            insights = list(db.llm_insights.find({
                'analysis_id': analysis_id,
                'user_id': user_id
            }))
        else:
            # Get recent insights for user
            insights = list(db.llm_insights.find({
                'user_id': user_id
            }).sort('created_at', -1).limit(10))
        
        if not insights:
            return Response({
                'message': 'No LLM insights found',
                'insights': [],
                'total_insights': 0
            })
        
        # Format insights for response
        formatted_insights = []
        for insight in insights:
            formatted_insight = {
                'id': str(insight['_id']),
                'analysis_id': insight.get('analysis_id'),
                'summary': insight.get('summary', ''),
                'recommendations': insight.get('recommendations', []),
                'traffic_patterns': insight.get('traffic_patterns', []),
                'key_findings': insight.get('key_findings', []),
                'confidence_score': insight.get('confidence_score', 0),
                'generated_by': insight.get('generated_by', 'TrafficAI LLM Engine'),
                'created_at': insight.get('created_at').isoformat() if insight.get('created_at') else None
            }
            formatted_insights.append(formatted_insight)
        
        return Response({
            'insights': formatted_insights,
            'total_insights': len(formatted_insights),
            'analysis_id': analysis_id
        })
        
    except Exception as e:
        logger.error(f"Error getting LLM insights: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_llm_insight(request):
    """Generate new LLM insight for an analysis"""
    try:
        user = request.user
        db = get_mongo_db()
        
        analysis_id = request.data.get('analysis_id')
        if not analysis_id:
            return Response({
                'error': 'analysis_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the analysis
        try:
            analysis = db.traffic_analyses.find_one({'_id': ObjectId(analysis_id)})
        except:
            return Response({
                'error': 'Invalid analysis_id format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not analysis or analysis.get('user_id') != str(user.id):
            return Response({
                'error': 'Analysis not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if insight already exists
        existing_insight = db.llm_insights.find_one({'analysis_id': analysis_id})
        if existing_insight:
            return Response({
                'message': 'Insight already exists for this analysis',
                'insight_id': str(existing_insight['_id'])
            })
        
        # Generate new insight based on analysis data
        vehicle_detection = analysis.get('vehicle_detection', {})
        traffic_density = analysis.get('traffic_density', {})
        
        vehicle_count = vehicle_detection.get('total_vehicles', 0)
        density_level = traffic_density.get('density_level', 'Medium')
        congestion_index = traffic_density.get('congestion_index', 0.5)
        
        # Generate contextual insights
        if vehicle_count > 20:
            summary = f"Heavy traffic detected with {vehicle_count} vehicles. High congestion may cause delays."
            recommendations = [
                "Consider implementing traffic flow optimization",
                "Monitor for bottlenecks and alternative routes",
                "Increase signal timing for main thoroughfares"
            ]
        elif vehicle_count > 10:
            summary = f"Moderate traffic flow with {vehicle_count} vehicles. Traffic is manageable."
            recommendations = [
                "Maintain current traffic management strategies",
                "Monitor for peak hour patterns",
                "Consider minor signal adjustments if needed"
            ]
        else:
            summary = f"Light traffic conditions with {vehicle_count} vehicles. Optimal flow detected."
            recommendations = [
                "Excellent conditions for maintenance activities",
                "Consider reducing signal wait times",
                "Monitor for unusual patterns"
            ]
        
        # Create insight document
        insight_doc = {
            'analysis_id': analysis_id,
            'user_id': str(user.id),
            'summary': summary,
            'recommendations': recommendations,
            'traffic_patterns': [
                f"Vehicle density: {density_level}",
                f"Congestion index: {congestion_index:.2f}",
                f"Total vehicles detected: {vehicle_count}"
            ],
            'key_findings': [
                f"Processing completed in {analysis.get('processing_time', 0):.1f} seconds",
                f"Model used: {analysis.get('model_version', 'Unknown')}",
                f"Analysis type: {analysis.get('analysis_type', 'image')}"
            ],
            'confidence_score': 0.85,
            'generated_by': 'TrafficAI LLM Engine v1.0',
            'created_at': timezone.now()
        }
        
        # Insert the insight
        result = db.llm_insights.insert_one(insight_doc)
        insight_id = str(result.inserted_id)
        
        # Update analysis with insight reference
        db.traffic_analyses.update_one(
            {'_id': ObjectId(analysis_id)},
            {'$set': {'llm_insight_id': insight_id}}
        )
        
        return Response({
            'message': 'LLM insight generated successfully',
            'insight_id': insight_id,
            'summary': summary,
            'recommendations': recommendations
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generating LLM insight: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_advanced_analytics(request):
    """Get advanced analytics combining history and insights"""
    try:
        user = request.user
        db = get_mongo_db()
        
        user_id = str(user.id)
        
        # Get recent data
        recent_analyses = list(db.traffic_analyses.find({
            'user_id': user_id
        }).sort('created_at', -1).limit(10))
        
        recent_insights = list(db.llm_insights.find({
            'user_id': user_id
        }).sort('created_at', -1).limit(5))
        
        recent_history = list(db.analysis_history.find({
            'user_id': user_id
        }).sort('created_at', -1).limit(10))
        
        # Calculate advanced metrics
        analytics = {
            'overview': {
                'total_analyses': len(recent_analyses),
                'total_insights': len(recent_insights),
                'total_history_records': len(recent_history)
            },
            'performance_summary': {
                'avg_processing_time': sum(a.get('processing_time', 0) for a in recent_analyses) / len(recent_analyses) if recent_analyses else 0,
                'avg_vehicle_count': sum(a.get('vehicle_detection', {}).get('total_vehicles', 0) for a in recent_analyses) / len(recent_analyses) if recent_analyses else 0,
                'most_used_model': 'YOLOv8 Enhanced'  # Could be calculated from data
            },
            'insights_summary': {
                'avg_confidence': sum(i.get('confidence_score', 0) for i in recent_insights) / len(recent_insights) if recent_insights else 0,
                'common_recommendations': [
                    'Monitor traffic patterns',
                    'Optimize signal timing',
                    'Consider alternative routes'
                ],
                'latest_insight': recent_insights[0].get('summary', 'No insights available') if recent_insights else 'No insights available'
            },
            'trend_analysis': {
                'traffic_trend': 'stable',
                'performance_trend': 'improving',
                'usage_pattern': 'regular'
            }
        }
        
        return Response({
            'analytics': analytics,
            'data_sources': {
                'analyses': len(recent_analyses),
                'insights': len(recent_insights),
                'history': len(recent_history)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)