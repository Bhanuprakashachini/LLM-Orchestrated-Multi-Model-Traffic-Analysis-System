"""
Comprehensive Model Comparison Views
Provides detailed tabular comparison of all models with metrics and recommendations
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
from pathlib import Path
import logging
import json
import csv
import io
import time

from .services.comprehensive_model_comparison import ComprehensiveModelComparison

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comprehensive_model_comparison(request):
    """
    Run comprehensive model comparison and return detailed tabular results
    """
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file
        if uploaded_file.size > 50 * 1024 * 1024:  # 50MB limit
            return Response({
                'error': 'File size exceeds 50MB limit'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save uploaded file
        timestamp = int(time.time())
        filename = f"comparison_{timestamp}_{uploaded_file.name}"
        file_path = default_storage.save(f'uploads/{filename}', ContentFile(uploaded_file.read()))
        full_file_path = default_storage.path(file_path)
        
        logger.info(f"Starting comprehensive model comparison for: {filename}")
        logger.info(f"Original filename: {uploaded_file.name}")
        logger.info(f"Saved filename: {filename}")
        logger.info(f"Full file path: {full_file_path}")
        
        # Check if original file is a video (use original filename for detection)
        original_ext = Path(uploaded_file.name).suffix.lower()
        is_video = original_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
        logger.info(f"File extension: {original_ext}, Is video: {is_video}")
        
        # Initialize comprehensive comparison service
        comparison_service = ComprehensiveModelComparison(device='auto')
        
        # Debug: Log service initialization
        logger.info(f"🔍 Initialized ComprehensiveModelComparison service with {len(comparison_service.models)} models")
        
        # Run comprehensive comparison (pass original filename for video detection)
        logger.info(f"🔄 Starting comprehensive comparison for: {full_file_path}")
        comparison_results = comparison_service.run_comprehensive_comparison(full_file_path, uploaded_file.name)
        
        # Debug: Log results summary
        vehicle_summary = comparison_results.get('vehicle_detection_summary', {})
        comparison_table = comparison_results.get('comparison_table', [])
        logger.info(f"🔍 API Results - Total vehicles: {vehicle_summary.get('total_vehicles', 0)}")
        logger.info(f"🔍 API Results - Best model: {vehicle_summary.get('best_model_used', 'Unknown')}")
        logger.info(f"🔍 API Results - Vehicle counts: {vehicle_summary.get('vehicle_counts', {})}")
        if comparison_table:
            logger.info(f"🔍 API Results - Top model from table: {comparison_table[0].get('model_name', 'Unknown')} with {comparison_table[0].get('total_vehicles', 0)} vehicles")
        
        # *** FORCE LLM INSIGHTS GENERATION IF MISSING ***
        llm_insights = comparison_results.get('llm_insights', {})
        if not llm_insights or not llm_insights.get('traffic_analysis'):
            logger.warning("LLM insights missing, generating directly...")
            try:
                # Generate LLM insights directly
                vehicle_summary = comparison_results.get('vehicle_detection_summary', {})
                comparison_table = comparison_results.get('comparison_table', [])
                
                # Force generation using the service method
                llm_insights = comparison_service._generate_llm_insights(vehicle_summary, comparison_table)
                
                if llm_insights and llm_insights.get('traffic_analysis'):
                    comparison_results['llm_insights'] = llm_insights
                    logger.info("✅ LLM insights generated directly and added to results")
                else:
                    logger.error("❌ Direct LLM insights generation also failed")
            except Exception as llm_error:
                logger.error(f"❌ Error generating LLM insights directly: {llm_error}")
        
        # Format results for frontend with enhanced vehicle detection data
        formatted_results = {
            'analysis_info': {
                'filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'total_models_compared': comparison_results['comparison_summary']['total_models_compared'],
                'analysis_time': f"{comparison_results['comparison_summary']['analysis_time']:.2f}s"
            },
            'comparison_table': comparison_results['comparison_table'],
            'performance_table': comparison_results['performance_table'],
            'detailed_metrics': comparison_results['detailed_metrics'],
            'recommendations': comparison_results['recommendations'],
            'use_case_recommendations': comparison_results['use_case_recommendations'],
            'model_selection_guide': comparison_results['model_selection_guide'],
            'advanced_features': comparison_results.get('advanced_features', {}),
            'vehicle_detection_summary': comparison_results.get('vehicle_detection_summary', {}),
            'images': comparison_results.get('saved_images', {}),
            'raw_results': comparison_results.get('raw_results', {})
        }
        
        # *** CRITICAL FIX: Add LLM insights to response ***
        llm_insights = comparison_results.get('llm_insights', {})
        logger.info(f"LLM insights from service: {type(llm_insights)} - {bool(llm_insights)}")
        
        if llm_insights:
            formatted_results['llm_insights'] = llm_insights
            logger.info(f"✅ LLM insights added to response: {len(llm_insights)} fields")
        else:
            logger.warning("❌ No LLM insights found in comparison results")
            # Add empty structure so frontend doesn't break
            formatted_results['llm_insights'] = {
                'traffic_analysis': 'AI insights temporarily unavailable',
                'model_used': 'Unknown',
                'confidence_score': 0.0,
                'generated_at': time.time(),
                'processing_time': 0.0,
                'error': 'LLM insights not generated'
            }
        
        # *** CRITICAL FIX: Save analysis results to MongoDB ***
        try:
            from .mongo_analysis import mongo_analysis
            
            # Get best model data for saving
            best_model = comparison_results['comparison_table'][0] if comparison_results['comparison_table'] else {}
            vehicle_summary = comparison_results.get('vehicle_detection_summary', {})
            
            # Calculate traffic density based on vehicle count
            total_vehicles = vehicle_summary.get('total_vehicles', 0)
            if total_vehicles == 0:
                density_level = 'Empty'
                congestion_index = 0.0
            elif total_vehicles <= 5:
                density_level = 'Low'
                congestion_index = 0.2
            elif total_vehicles <= 15:
                density_level = 'Medium'
                congestion_index = 0.5
            elif total_vehicles <= 25:
                density_level = 'High'
                congestion_index = 0.8
            else:
                density_level = 'Congested'
                congestion_index = 1.0
            
            # Prepare analysis data for MongoDB
            analysis_data = {
                'original_image_path': file_path,
                'file_size': uploaded_file.size,
                'image_dimensions': comparison_results.get('analysis_metadata', {}).get('image_dimensions', {}),
                'vehicle_detection': {
                    'total_vehicles': total_vehicles,
                    'detection_summary': vehicle_summary.get('vehicle_counts', {}),
                    'best_model_used': vehicle_summary.get('best_model_used', best_model.get('model_name', 'Unknown')),
                    'detection_quality': vehicle_summary.get('detection_quality', 'Good'),
                    'average_confidence': 0.0,  # Removed confidence display
                    'detections': []  # Will be populated by mongo service
                },
                'traffic_density': {
                    'density_level': density_level,
                    'congestion_index': congestion_index,
                    'flow_state': 'Normal' if congestion_index < 0.7 else 'Congested'
                },
                'processing_time': comparison_results['comparison_summary']['analysis_time'],
                'fps': float(best_model.get('fps', '0 FPS').replace(' FPS', '')),
                'model_version': f"Comprehensive ({best_model.get('model_name', 'Unknown')})",
                'analysis_type': 'comprehensive_comparison'
            }
            
            # Save to MongoDB with full data population
            analysis_id = mongo_analysis.create_analysis(request.user.id, analysis_data)
            
            if analysis_id:
                # Add analysis ID to results
                formatted_results['analysis_id'] = analysis_id
                formatted_results['comparison_summary'] = {
                    'analysis_id': analysis_id,
                    'total_models_compared': comparison_results['comparison_summary']['total_models_compared'],
                    'analysis_time': comparison_results['comparison_summary']['analysis_time'],
                    'best_model': best_model.get('model_name', 'Unknown'),
                    'saved_to_database': True,
                    'database_type': 'MongoDB'
                }
                
                logger.info(f"✅ Analysis saved to MongoDB with ID: {analysis_id}")
            else:
                raise Exception("Failed to create analysis in MongoDB")
            
        except Exception as save_error:
            logger.error(f"❌ Failed to save analysis to MongoDB: {save_error}")
            # Don't fail the entire request, just log the error
            formatted_results['comparison_summary'] = {
                'analysis_id': 'unsaved',
                'total_models_compared': comparison_results['comparison_summary']['total_models_compared'],
                'analysis_time': comparison_results['comparison_summary']['analysis_time'],
                'best_model': best_model.get('model_name', 'Unknown'),
                'saved_to_database': False,
                'database_type': 'MongoDB',
                'save_error': str(save_error)
            }
        
        logger.info(f"Comprehensive comparison completed: {len(comparison_results['comparison_table'])} models analyzed")
        
        return Response(formatted_results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in comprehensive model comparison: {str(e)}")
        return Response({
            'error': f'Comprehensive comparison failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_model_justification(request):
    """
    Get detailed justification for choosing a specific model
    """
    try:
        model_name = request.data.get('model_name')
        comparison_data = request.data.get('comparison_results')
        
        if not model_name:
            return Response({
                'error': 'Model name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not comparison_data:
            return Response({
                'error': 'Comparison results are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize comparison service
        comparison_service = ComprehensiveModelComparison(device='auto')
        
        # Get model justification
        justification = comparison_service.get_model_justification(model_name, comparison_data)
        
        if 'error' in justification:
            return Response(justification, status=status.HTTP_404_NOT_FOUND)
        
        return Response(justification, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting model justification: {str(e)}")
        return Response({
            'error': f'Failed to get model justification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_comparison_csv(request):
    """
    Export comparison results to CSV format
    """
    try:
        comparison_data = request.data.get('comparison_results')
        
        if not comparison_data:
            return Response({
                'error': 'Comparison results are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create CSV content
        output = io.StringIO()
        
        # Write main comparison table
        comparison_table = comparison_data.get('comparison_table', [])
        if comparison_table:
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['COMPREHENSIVE MODEL COMPARISON REPORT'])
            writer.writerow(['Generated on:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')])
            writer.writerow([])
            
            # Write comparison table
            writer.writerow(['MODEL COMPARISON TABLE'])
            headers = [
                'Model Name', 'Type', 'Accuracy Tier', 'Vehicles Detected',
                'Estimated Accuracy', 'Estimated Recall', 'F1-Score', 'Processing Time',
                'FPS', 'CPU Usage', 'Memory Usage', 'GPU Usage', 'Overall Score', 'Grade'
            ]
            writer.writerow(headers)
            
            for row in comparison_table:
                csv_row = [
                    row['model_name'],
                    row['model_type'],
                    row['accuracy_tier'],
                    row['total_vehicles'],
                    row['avg_confidence'],
                    row['estimated_accuracy'],
                    row['estimated_recall'],
                    row['f1_score'],
                    row['processing_time'],
                    row['fps'],
                    row['cpu_usage'],
                    row['memory_usage'],
                    row['gpu_usage'],
                    row['overall_score'],
                    row['grade']
                ]
                writer.writerow(csv_row)
            
            writer.writerow([])
            
            # Write detailed metrics
            detailed_metrics = comparison_data.get('detailed_metrics', {})
            
            # Accuracy metrics
            if 'accuracy_metrics' in detailed_metrics:
                writer.writerow(['ACCURACY METRICS'])
                writer.writerow(detailed_metrics['accuracy_metrics']['headers'])
                for row in detailed_metrics['accuracy_metrics']['rows']:
                    writer.writerow(row)
                writer.writerow([])
            
            # Performance metrics
            if 'performance_metrics' in detailed_metrics:
                writer.writerow(['PERFORMANCE METRICS'])
                writer.writerow(detailed_metrics['performance_metrics']['headers'])
                for row in detailed_metrics['performance_metrics']['rows']:
                    writer.writerow(row)
                writer.writerow([])
            
            # Detection metrics
            if 'detection_metrics' in detailed_metrics:
                writer.writerow(['DETECTION METRICS'])
                writer.writerow(detailed_metrics['detection_metrics']['headers'])
                for row in detailed_metrics['detection_metrics']['rows']:
                    writer.writerow(row)
                writer.writerow([])
            
            # Recommendations
            recommendations = comparison_data.get('recommendations', {})
            if recommendations:
                writer.writerow(['RECOMMENDATIONS'])
                if recommendations.get('best_overall'):
                    writer.writerow(['Best Overall:', recommendations['best_overall']['model'], recommendations['best_overall']['reason']])
                if recommendations.get('best_accuracy'):
                    writer.writerow(['Best Accuracy:', recommendations['best_accuracy']['model'], recommendations['best_accuracy']['reason']])
                if recommendations.get('best_speed'):
                    writer.writerow(['Best Speed:', recommendations['best_speed']['model'], recommendations['best_speed']['reason']])
        
        # Create HTTP response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="model_comparison_{int(time.time())}.csv"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting comparison CSV: {str(e)}")
        return Response({
            'error': f'Failed to export CSV: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_available_models(request):
    """
    Get list of available models for comparison
    """
    try:
        comparison_service = ComprehensiveModelComparison(device='auto')
        
        models_info = []
        for model_key, model_info in comparison_service.models.items():
            models_info.append({
                'key': model_key,
                'name': model_info['name'],
                'description': model_info['description'],
                'type': model_info['type'],
                'accuracy_tier': model_info['accuracy_tier'],
                'use_case': model_info['use_case'],
                'pros': model_info['pros'],
                'cons': model_info['cons'],
                'recommended_for': model_info['recommended_for']
            })
        
        return Response({
            'total_models': len(models_info),
            'models': models_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return Response({
            'error': f'Failed to get available models: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_model_selection_guide(request):
    """
    Get comprehensive model selection guide
    """
    try:
        comparison_service = ComprehensiveModelComparison(device='auto')
        guide = comparison_service._generate_model_selection_guide()
        
        return Response(guide, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting model selection guide: {str(e)}")
        return Response({
            'error': f'Failed to get model selection guide: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)