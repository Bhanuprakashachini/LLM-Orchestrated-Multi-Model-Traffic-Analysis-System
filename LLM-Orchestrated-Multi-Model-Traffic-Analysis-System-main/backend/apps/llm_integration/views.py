"""
LLM Integration Views for Traffic Analysis Intelligence
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from .services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_feature_insights(request):
    """
    Generate feature-specific AI insights for analysis results
    """
    try:
        analysis_data = request.data.get('analysis_data')
        feature_type = request.data.get('feature_type')
        
        if not analysis_data:
            return Response({
                'error': 'Analysis data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not feature_type:
            return Response({
                'error': 'Feature type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate feature type
        valid_features = ['vehicle-detection', 'traffic-density', 'model-comparison', 'visualization', 'history-reports']
        if feature_type not in valid_features:
            return Response({
                'error': f'Invalid feature type. Must be one of: {", ".join(valid_features)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use LLM service to generate feature-specific insights
        llm_service = LLMService()
        result = llm_service.generate_feature_specific_insights(
            analysis_data=analysis_data,
            feature_type=feature_type,
            user_id=str(request.user.id)
        )
        
        if result.get('success'):
            return Response({
                'success': True,
                'insight': result.get('insight'),
                'feature_type': result.get('feature_type'),
                'model_used': result.get('model_used'),
                'analysis_summary': result.get('analysis_summary'),
                'generated_at': result.get('generated_at')
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to generate insights'),
                'feature_type': feature_type
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Feature insights generation failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_traffic_conditions(request):
    """
    Feature 8: LLM-Based Decision Making
    Analyze traffic data and generate human-readable explanations
    """
    try:
        analysis_id = request.data.get('analysis_id')
        analysis_data = request.data.get('analysis_data')
        
        if not analysis_data and analysis_id:
            # Get analysis data from database
            try:
                analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
                analysis_data = {
                    'vehicle_detection': analysis.vehicle_detection,
                    'traffic_density': analysis.traffic_density,
                    'performance_metrics': {
                        'processing_time': analysis.processing_time,
                        'fps': analysis.fps,
                        'model_version': analysis.model_version
                    }
                }
            except AnalysisResult.DoesNotExist:
                return Response({
                    'error': 'Analysis not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if not analysis_data:
            return Response({
                'error': 'Analysis data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use LLM service to analyze conditions
        llm_service = LLMService()
        result = llm_service.analyze_traffic_conditions(analysis_data, request.user.id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in traffic condition analysis: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_model_performance(request):
    """
    Feature 9: LLM-Based Model Comparison
    Compare YOLOv8 and YOLOv12 performance using LLM analysis
    """
    try:
        yolov8_results = request.data.get('yolov8_results')
        yolov12_results = request.data.get('yolov12_results')
        
        if not yolov8_results or not yolov12_results:
            return Response({
                'error': 'Both YOLOv8 and YOLOv12 results are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use LLM service to compare models
        llm_service = LLMService()
        result = llm_service.compare_model_performance(yolov8_results, yolov12_results, request.user.id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in model comparison: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_traffic_summary(request):
    """
    Feature 10: LLM-Based Traffic Summary Generation
    Generate concise traffic summary in simple language
    """
    try:
        analysis_id = request.data.get('analysis_id')
        analysis_data = request.data.get('analysis_data')
        
        if not analysis_data and analysis_id:
            # Get analysis data from database
            try:
                analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
                analysis_data = {
                    'vehicle_detection': analysis.vehicle_detection,
                    'traffic_density': analysis.traffic_density
                }
            except AnalysisResult.DoesNotExist:
                return Response({
                    'error': 'Analysis not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if not analysis_data:
            return Response({
                'error': 'Analysis data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use LLM service to generate summary
        llm_service = LLMService()
        result = llm_service.generate_traffic_summary(analysis_data, request.user.id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating traffic summary: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_recommendations(request):
    """
    Feature 11: LLM-Based Insight & Recommendation
    Provide actionable traffic management recommendations
    """
    try:
        analysis_id = request.data.get('analysis_id')
        analysis_data = request.data.get('analysis_data')
        
        if not analysis_data and analysis_id:
            # Get analysis data from database
            try:
                analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
                analysis_data = {
                    'vehicle_detection': analysis.vehicle_detection,
                    'traffic_density': analysis.traffic_density
                }
            except AnalysisResult.DoesNotExist:
                return Response({
                    'error': 'Analysis not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if not analysis_data:
            return Response({
                'error': 'Analysis data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use LLM service to generate recommendations
        llm_service = LLMService()
        result = llm_service.generate_recommendations(analysis_data, request.user.id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_natural_language_query(request):
    """
    Feature 12: LLM-Based Natural Language Query Handling
    Answer user questions about traffic analysis
    """
    try:
        query = request.data.get('query')
        analysis_id = request.data.get('analysis_id')
        analysis_data = request.data.get('analysis_data')
        
        if not query:
            return Response({
                'error': 'Query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not analysis_data and analysis_id:
            # Get analysis data from database
            try:
                analysis = AnalysisResult.objects.get(id=analysis_id, user=request.user)
                analysis_data = {
                    'vehicle_detection': analysis.vehicle_detection,
                    'traffic_density': analysis.traffic_density,
                    'performance_metrics': {
                        'processing_time': analysis.processing_time,
                        'fps': analysis.fps,
                        'model_version': analysis.model_version
                    }
                }
            except AnalysisResult.DoesNotExist:
                return Response({
                    'error': 'Analysis not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if not analysis_data:
            analysis_data = {}  # Allow queries without specific analysis data
        
        # Use LLM service to handle query
        llm_service = LLMService()
        result = llm_service.handle_natural_language_query(query, analysis_data, request.user.id)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error handling natural language query: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_traffic_insights(request):
    """Get user's traffic insights history"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        insight_type = request.GET.get('type', None)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query
        query = TrafficInsight.objects.filter(user=request.user)
        if insight_type:
            query = query.filter(insight_type=insight_type)
        
        # Get insights
        insights = query.order_by('-created_at')[offset:offset + page_size]
        total_count = query.count()
        
        # Serialize results
        results = []
        for insight in insights:
            results.append({
                'id': insight.id,
                'insight_type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'confidence_score': insight.confidence_score,
                'recommendations': insight.recommendations,
                'created_at': insight.created_at.isoformat(),
                'data_points': insight.data_points
            })
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting traffic insights: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scene_descriptions(request):
    """Get user's scene descriptions history"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get descriptions
        descriptions = SceneDescription.objects.filter(
            user=request.user
        ).order_by('-created_at')[offset:offset + page_size]
        
        total_count = SceneDescription.objects.filter(user=request.user).count()
        
        # Serialize results
        results = []
        for desc in descriptions:
            results.append({
                'id': desc.id,
                'description': desc.description,
                'key_observations': desc.key_observations,
                'traffic_conditions': desc.traffic_conditions,
                'weather_assessment': desc.weather_assessment,
                'recommendations': desc.recommendations,
                'created_at': desc.created_at.isoformat()
            })
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error getting scene descriptions: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_history(request):
    """Get user's conversation history"""
    try:
        session_id = request.GET.get('session_id')
        
        if session_id:
            # Get specific conversation
            try:
                session = ConversationSession.objects.get(id=session_id, user=request.user)
                messages = LLMMessage.objects.filter(session=session).order_by('created_at')
                
                conversation = {
                    'session_id': session.id,
                    'context_type': session.context_type,
                    'created_at': session.created_at.isoformat(),
                    'message_count': session.message_count,
                    'messages': []
                }
                
                for message in messages:
                    conversation['messages'].append({
                        'id': message.id,
                        'role': message.role,
                        'content': message.content,
                        'created_at': message.created_at.isoformat(),
                        'token_count': message.token_count
                    })
                
                return Response(conversation)
                
            except ConversationSession.DoesNotExist:
                return Response({
                    'error': 'Conversation session not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get all conversations
            sessions = ConversationSession.objects.filter(
                user=request.user
            ).order_by('-created_at')[:20]
            
            conversations = []
            for session in sessions:
                conversations.append({
                    'session_id': session.id,
                    'context_type': session.context_type,
                    'created_at': session.created_at.isoformat(),
                    'message_count': session.message_count,
                    'last_message_at': session.updated_at.isoformat()
                })
            
            return Response({
                'conversations': conversations,
                'total_sessions': len(conversations)
            })
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, session_id):
    """Delete a conversation session"""
    try:
        session = ConversationSession.objects.get(id=session_id, user=request.user)
        session.delete()
        
        return Response({
            'message': 'Conversation deleted successfully'
        })
        
    except ConversationSession.DoesNotExist:
        return Response({
            'error': 'Conversation session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)