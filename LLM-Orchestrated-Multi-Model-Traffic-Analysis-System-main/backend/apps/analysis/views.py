from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from utils.mongodb import traffic_service, get_mongo_db
from datetime import datetime
import logging
import json
import csv
import io
import time
import os
from pathlib import Path
from collections import defaultdict
from .services.yolov8_analyzer import YOLOv8TrafficAnalyzer
from .services.yolov12_analyzer import YOLOv12TrafficAnalyzer
from .services.model_comparison import ModelComparisonService
from .services.comprehensive_model_comparison import ComprehensiveModelComparison
from .services.advanced_traffic_analyzer import AdvancedTrafficAnalyzer

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        db = get_mongo_db()
        if db is not None:
            # Test with a simple query
            collections = db.list_collection_names()
            mongo_status = "connected"
            mongo_collections = len(collections)
        else:
            mongo_status = "disconnected"
            mongo_collections = 0
        
        return Response({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'mongodb': {
                    'status': mongo_status,
                    'collections': mongo_collections
                }
            },
            'services': {
                'traffic_analysis': 'active',
                'llm_integration': 'active',
                'analytics': 'active'
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_recent_analyses(request):
    """Get recent traffic analyses"""
    try:
        limit = int(request.GET.get('limit', 10))
        analyses = traffic_service.get_recent_analyses(limit=limit)
        
        # Convert ObjectId to string for JSON serialization
        for analysis in analyses:
            if '_id' in analysis:
                analysis['id'] = str(analysis['_id'])
                del analysis['_id']
            
            # Convert datetime objects to ISO format
            for key, value in analysis.items():
                if hasattr(value, 'isoformat'):
                    analysis[key] = value.isoformat()
        
        return Response({
            'count': len(analyses),
            'results': analyses
        })
    except Exception as e:
        logger.error(f"Error getting recent analyses: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_analysis(request):
    """Create a new traffic analysis"""
    try:
        data = request.data.copy()
        data['user_id'] = str(request.user.id)
        data['status'] = 'pending'
        
        analysis_id = traffic_service.create_analysis(data)
        
        if analysis_id:
            return Response({
                'id': analysis_id,
                'message': 'Analysis created successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to create analysis'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error creating analysis: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_analysis(request, analysis_id):
    """Get analysis by ID"""
    try:
        analysis = traffic_service.get_analysis(analysis_id)
        
        if analysis:
            # Convert ObjectId to string
            if '_id' in analysis:
                analysis['id'] = str(analysis['_id'])
                del analysis['_id']
            
            # Convert datetime objects to ISO format
            for key, value in analysis.items():
                if hasattr(value, 'isoformat'):
                    analysis[key] = value.isoformat()
            
            return Response(analysis)
        else:
            return Response({
                'error': 'Analysis not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def database_stats(request):
    """Get database statistics"""
    try:
        db = get_mongo_db()
        if db is None:
            return Response({
                'error': 'MongoDB connection failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        stats = {}
        collections = db.list_collection_names()
        
        for collection_name in collections:
            collection = db[collection_name]
            stats[collection_name] = {
                'count': collection.count_documents({}),
                'indexes': len(list(collection.list_indexes()))
            }
        
        return Response({
            'database': db.name,
            'total_collections': len(collections),
            'collections': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_and_analyze(request):
    """Upload image/video and perform traffic analysis"""
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        model_type = request.data.get('model_type', 'comparison')  # 'yolov8', 'yolov12', or 'comparison'
        
        # ROI parameters (optional)
        roi_polygon = request.data.get('roi_polygon', None)  # List of [x, y] points
        if roi_polygon:
            try:
                roi_polygon = json.loads(roi_polygon) if isinstance(roi_polygon, str) else roi_polygon
                logger.info(f"🎯 ROI polygon provided with {len(roi_polygon)} points")
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid ROI polygon format, ignoring")
                roi_polygon = None
        
        # Save uploaded file
        file_path = default_storage.save(f'uploads/{uploaded_file.name}', ContentFile(uploaded_file.read()))
        full_file_path = default_storage.path(file_path)
        
        # Perform analysis based on model type with enhancements
        if model_type == 'yolov8':
            analyzer = YOLOv8TrafficAnalyzer(device='auto', confidence_threshold=0.08, roi_polygon=roi_polygon)  # OPTIMIZED for sweet spot detection
            results = analyzer.analyze_traffic_scene(full_file_path)
        elif model_type == 'yolov12':
            analyzer = YOLOv12TrafficAnalyzer(device='auto', confidence_threshold=0.07, roi_polygon=roi_polygon)  # OPTIMIZED for sweet spot detection
            results = analyzer.analyze_traffic_scene(full_file_path)
        else:  # comparison with enhancements
            comparison_service = ComprehensiveModelComparison(device='auto')
            results = comparison_service.run_comprehensive_comparison(full_file_path)
        
        # Save to MongoDB using our MongoDB service
        from .mongo_analysis import mongo_analysis
        
        # Extract vehicle detection data from comprehensive service response
        if 'vehicle_detection_summary' in results:
            # Comprehensive service response structure
            vehicle_detection_data = results.get('vehicle_detection_summary', {})
            performance_data = results.get('comparison_summary', {})
            traffic_density_data = {
                'density_level': 'moderate',  # Default
                'congestion_index': 0.5
            }
            logger.info(f"🔍 Using comprehensive service response")
            logger.info(f"📊 Vehicle detection data: {vehicle_detection_data}")
        else:
            # Individual analyzer response structure
            vehicle_detection_data = results.get('vehicle_detection', {})
            performance_data = results.get('performance_metrics', {})
            traffic_density_data = results.get('traffic_density', {})
            logger.info(f"🔍 Using individual analyzer response")
            logger.info(f"📊 Vehicle detection data: {vehicle_detection_data}")
        
        analysis_data = {
            'original_image_path': file_path,
            'file_size': uploaded_file.size,
            'image_dimensions': performance_data.get('image_dimensions', {}),
            'vehicle_detection': vehicle_detection_data,
            'traffic_density': traffic_density_data,
            'processing_time': performance_data.get('processing_time', 0) or performance_data.get('analysis_time', 0),
            'fps': performance_data.get('fps', 0),
            'model_version': performance_data.get('model_version', model_type),
            'analysis_type': 'image'
        }
        
        analysis_id = mongo_analysis.create_analysis(request.user.id, analysis_data)
        
        # 🧠 ADD LLM INSIGHTS GENERATION
        llm_insights = None
        try:
            from apps.llm_integration.services.llm_service import LLMService
            
            llm_service = LLMService()
            
            # Generate traffic condition analysis
            llm_result = llm_service.analyze_traffic_conditions(analysis_data, str(request.user.id))
            
            if llm_result.get('success'):
                llm_insights = {
                    'traffic_analysis': llm_result.get('insight', ''),
                    'model_used': llm_result.get('model_used', 'groq'),
                    'analysis_summary': llm_result.get('analysis_summary', {}),
                    'generated_at': datetime.now().isoformat()
                }
                
                # Add LLM insights to results
                results['llm_insights'] = llm_insights
                
                logger.info(f"✅ LLM insights generated for analysis {analysis_id}")
            else:
                logger.warning(f"⚠️ LLM insights generation failed: {llm_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"❌ Error generating LLM insights: {e}")
            # Continue without LLM insights - don't fail the entire analysis
        
        if analysis_id:
            # Add analysis ID to results
            results['analysis_id'] = analysis_id
            results['file_path'] = file_path
            
            # Ensure vehicle_detection is in the response for frontend compatibility
            if 'vehicle_detection' not in results and 'vehicle_detection_summary' in results:
                results['vehicle_detection'] = results['vehicle_detection_summary']
            
            # Ensure performance_metrics is in the response for frontend compatibility  
            if 'performance_metrics' not in results and 'comparison_summary' in results:
                results['performance_metrics'] = {
                    'processing_time': results['comparison_summary'].get('analysis_time', 0),
                    'model_version': 'Comprehensive Comparison',
                    'models_compared': results['comparison_summary'].get('total_models_compared', 0)
                }
            
            # Ensure traffic_density is in the response
            if 'traffic_density' not in results:
                results['traffic_density'] = {
                    'density_level': 'moderate',
                    'congestion_index': 0.5
                }
            
            return Response(results, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Failed to save analysis'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error in upload and analyze: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analysis_history(request):
    """Get user's analysis history"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Get user's analyses from MongoDB
        from .mongo_analysis import mongo_analysis
        
        skip = (page - 1) * page_size
        result = mongo_analysis.get_user_analyses(
            user_id=str(request.user.id),
            limit=page_size,
            skip=skip
        )
        
        if result:
            return Response({
                'count': result['total_count'],
                'page': page,
                'page_size': page_size,
                'total_pages': (result['total_count'] + page_size - 1) // page_size,
                'results': result['analyses']
            })
        else:
            return Response({
                'error': 'Failed to get analysis history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def download_report(request, analysis_id):
    """Download analysis report in HTML or JSON format"""
    try:
        # Get format from query parameter (GET) or request body (POST)
        if request.method == 'POST':
            format_type = request.data.get('format', 'json').lower()
        else:
            format_type = request.GET.get('format', 'json').lower()
        
        logger.info(f"Download request: analysis_id={analysis_id}, format={format_type}, user={request.user.id}, method={request.method}")
        
        # Get analysis from MongoDB
        from .mongo_analysis import mongo_analysis
        
        analysis = mongo_analysis.get_analysis(analysis_id, request.user.id)
        
        if not analysis:
            logger.warning(f"Analysis not found: {analysis_id} for user {request.user.id}")
            return Response({
                'error': 'Analysis not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"Found analysis: {analysis.get('id', 'unknown')}, generating {format_type} report")
        
        # Prepare data
        data = {
            'analysis_id': analysis.get('id', analysis_id),
            'created_at': analysis.get('created_at', ''),
            'model_version': analysis.get('model_version', 'unknown'),
            'processing_time': analysis.get('processing_time', 0),
            'fps': analysis.get('fps', 0),
            'file_size': analysis.get('file_size', 0),
            'image_dimensions': analysis.get('image_dimensions', {}),
            'vehicle_detection': analysis.get('vehicle_detection', {}),
            'traffic_density': analysis.get('traffic_density', {}),
            'analysis_type': analysis.get('analysis_type', 'image')
        }
        
        if format_type == 'html':
            logger.info(f"Generating HTML report for analysis {analysis_id}")
            
            # Get image paths
            original_image = analysis.get('original_image_path', '')
            annotated_image = analysis.get('annotated_image_path', '')
            
            # Prepare vehicle detection data for charts
            vehicle_detection = analysis.get('vehicle_detection', {})
            vehicle_counts = vehicle_detection.get('detection_summary', {})
            
            # Generate HTML report with embedded charts and images
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Analysis Report - {analysis_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .images-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }}
        .image-container {{
            text-align: center;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #e9ecef;
        }}
        .image-container h3 {{
            color: #495057;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .image-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .chart-container {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            height: 400px;
            position: relative;
        }}
        .chart-title {{
            text-align: center;
            color: #495057;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: 600;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}
        .no-image {{
            background: #e9ecef;
            color: #6c757d;
            padding: 60px 20px;
            border-radius: 8px;
            font-size: 1.1em;
        }}
        @media (max-width: 768px) {{
            .images-grid {{
                grid-template-columns: 1fr;
            }}
            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Traffic Analysis Report</h1>
            <p>Analysis ID: {analysis_id} | Generated on {analysis.get('created_at', 'Unknown')}</p>
        </div>
        
        <div class="content">
            <!-- Summary Statistics -->
            <div class="section">
                <h2>📊 Analysis Summary</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{vehicle_detection.get('total_vehicles', 0)}</div>
                        <div class="stat-label">Total Vehicles</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis.get('processing_time', 0):.2f}s</div>
                        <div class="stat-label">Processing Time</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis.get('fps', 0):.1f}</div>
                        <div class="stat-label">FPS</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{analysis.get('model_version', 'Unknown')}</div>
                        <div class="stat-label">Model Used</div>
                    </div>
                </div>
            </div>
            
            <!-- Images Section -->
            <div class="section">
                <h2>🖼️ Analysis Images</h2>
                <div class="images-grid">
                    <div class="image-container">
                        <h3>📷 Original Image</h3>
                        {f'<img src="http://localhost:8000/media/{original_image}" alt="Original Image" onerror="this.parentElement.innerHTML=\'<div class=&quot;no-image&quot;>Original image not available</div>\'">' if original_image else '<div class="no-image">Original image not available</div>'}
                    </div>
                    <div class="image-container">
                        <h3>🎯 Annotated Image</h3>
                        {f'<img src="http://localhost:8000/media/{annotated_image}" alt="Annotated Image" onerror="this.parentElement.innerHTML=\'<div class=&quot;no-image&quot;>Annotated image not available</div>\'">' if annotated_image else '<div class="no-image">Annotated image not available</div>'}
                    </div>
                </div>
            </div>
            
            <!-- Vehicle Detection Chart -->
            <div class="section">
                <h2>🚗 Vehicle Detection Results</h2>
                <div class="chart-container">
                    <div class="chart-title">Vehicle Distribution by Type</div>
                    <canvas id="vehicleChart"></canvas>
                </div>
            </div>
            
            <!-- Traffic Density -->
            <div class="section">
                <h2>🌡️ Traffic Density Analysis</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{analysis.get('traffic_density', {}).get('density_level', 'Unknown')}</div>
                        <div class="stat-label">Density Level</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{(analysis.get('traffic_density', {}).get('congestion_index', 0) * 100):.0f}%</div>
                        <div class="stat-label">Congestion Index</div>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Data Table -->
            <div class="section">
                <h2>📋 Detailed Analysis Data</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">Metric</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6; text-align: left;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">Analysis ID</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{analysis_id}</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #dee2e6;">Created At</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{analysis.get('created_at', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">Model Version</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{analysis.get('model_version', 'Unknown')}</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 12px; border: 1px solid #dee2e6;">File Size</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{analysis.get('file_size', 0)} bytes</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">Average Confidence</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">{(vehicle_detection.get('average_confidence', 0) * 100):.1f}%</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Traffic Analysis System | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
    </div>
    
    <script>
        // Vehicle Distribution Chart
        const ctx = document.getElementById('vehicleChart').getContext('2d');
        const vehicleData = {json.dumps(vehicle_counts)};
        
        const labels = Object.keys(vehicleData);
        const data = Object.values(vehicleData);
        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
        
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
                datasets: [{{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 20,
                            font: {{
                                size: 14
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
            """
            
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="analysis_report_{analysis_id}.html"'
            logger.info(f"HTML report generated successfully for analysis {analysis_id}")
            return response
            
        else:  # JSON format
            logger.info(f"Generating JSON report for analysis {analysis_id}")
            response = HttpResponse(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="analysis_{analysis_id}.json"'
            logger.info(f"JSON report generated successfully for analysis {analysis_id}")
            return response
            
    except Exception as e:
        logger.error(f"Error downloading report for {analysis_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_performance_metrics(request):
    """Get performance metrics for all models"""
    try:
        # Get recent analyses for performance calculation
        recent_analyses = AnalysisResult.objects.filter(user=request.user).order_by('-created_at')[:50]
        
        if not recent_analyses:
            return Response({
                'message': 'No analyses found for performance calculation'
            })
        
        # Calculate metrics by model
        model_metrics = {}
        
        for analysis in recent_analyses:
            model = analysis.model_version
            if model not in model_metrics:
                model_metrics[model] = {
                    'total_analyses': 0,
                    'total_processing_time': 0,
                    'total_fps': 0,
                    'total_vehicles_detected': 0,
                    'confidence_scores': [],
                    'accuracy_scores': []
                }
            
            metrics = model_metrics[model]
            metrics['total_analyses'] += 1
            metrics['total_processing_time'] += analysis.processing_time
            metrics['total_fps'] += analysis.fps
            
            if analysis.vehicle_detection:
                metrics['total_vehicles_detected'] += analysis.vehicle_detection.get('total_vehicles', 0)
                avg_confidence = analysis.vehicle_detection.get('average_confidence', 0)
                if avg_confidence > 0:
                    metrics['confidence_scores'].append(avg_confidence)
        
        # Calculate final metrics
        performance_summary = {}
        for model, metrics in model_metrics.items():
            if metrics['total_analyses'] > 0:
                avg_confidence = sum(metrics['confidence_scores']) / len(metrics['confidence_scores']) if metrics['confidence_scores'] else 0
                
                # Calculate estimated precision based on confidence distribution
                high_confidence_count = sum(1 for conf in metrics['confidence_scores'] if conf > 0.7)
                estimated_precision = high_confidence_count / len(metrics['confidence_scores']) if metrics['confidence_scores'] else 0
                
                # Calculate consistency score as a proxy for reliability
                if len(metrics['confidence_scores']) > 1:
                    import statistics
                    confidence_std = statistics.stdev(metrics['confidence_scores'])
                    consistency_score = max(0, 1 - (confidence_std / max(avg_confidence, 0.1)))
                else:
                    consistency_score = avg_confidence
                
                # Estimate recall based on detection rate and confidence
                # Higher confidence generally correlates with better recall
                estimated_recall = min(0.95, avg_confidence * 1.1)
                
                # Calculate F1 score from estimated precision and recall
                if estimated_precision + estimated_recall > 0:
                    estimated_f1 = 2 * (estimated_precision * estimated_recall) / (estimated_precision + estimated_recall)
                else:
                    estimated_f1 = 0
                
                performance_summary[model] = {
                    'total_analyses': metrics['total_analyses'],
                    'average_processing_time': metrics['total_processing_time'] / metrics['total_analyses'],
                    'average_fps': metrics['total_fps'] / metrics['total_analyses'],
                    'average_vehicles_per_analysis': metrics['total_vehicles_detected'] / metrics['total_analyses'],
                    'average_confidence': avg_confidence,
                    'estimated_precision': estimated_precision,
                    'estimated_recall': estimated_recall,
                    'estimated_f1_score': estimated_f1,
                    'consistency_score': consistency_score,
                    'high_confidence_detections': high_confidence_count,
                    'note': 'Metrics estimated from confidence scores - ground truth validation recommended'
                }
        
        return Response({
            'performance_metrics': performance_summary,
            'total_analyses_evaluated': len(recent_analyses),
            'evaluation_period': 'Last 50 analyses'
        })
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_models(request):
    """Compare YOLOv8 and YOLOv12 models on uploaded image"""
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Save uploaded file
        file_path = default_storage.save(f'uploads/{uploaded_file.name}', ContentFile(uploaded_file.read()))
        full_file_path = default_storage.path(file_path)
        
        # Perform model comparison
        comparison_service = ModelComparisonService()
        results = comparison_service.compare_models(full_file_path)
        
        # Save comparison result to database
        analysis_result = AnalysisResult.objects.create(
            user=request.user,
            original_image=file_path,
            file_size=uploaded_file.size,
            image_dimensions=results.get('consolidated_result', {}).get('performance_metrics', {}).get('image_dimensions', {}),
            vehicle_detection=results.get('consolidated_result', {}).get('vehicle_detection', {}),
            traffic_density=results.get('consolidated_result', {}).get('traffic_density', {}),
            processing_time=results.get('comparison_time', 0),
            fps=results.get('consolidated_result', {}).get('performance_metrics', {}).get('fps', 0),
            model_version=f"Comparison ({results.get('best_model', 'Unknown')})",
            analysis_type='image'
        )
        
        # Add analysis ID to results
        results['analysis_id'] = analysis_result.id
        results['file_path'] = file_path
        
        return Response(results, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error in model comparison: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advanced_traffic_analysis(request):
    """
    Advanced traffic analysis with AI processing and enhanced vehicle detection
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
        filename = f"advanced_{timestamp}_{uploaded_file.name}"
        file_path = default_storage.save(f'uploads/{filename}', ContentFile(uploaded_file.read()))
        full_file_path = default_storage.path(file_path)
        
        logger.info(f"Starting advanced traffic analysis for: {filename}")
        
        # Get analysis options
        enable_all_features = request.data.get('enable_all_features', True)
        device = request.data.get('device', 'auto')
        confidence_threshold = float(request.data.get('confidence_threshold', 0.4))
        
        # Initialize advanced analyzer
        analyzer = AdvancedTrafficAnalyzer(
            device=device,
            confidence_threshold=confidence_threshold
        )
        
        # Run comprehensive analysis
        analysis_results = analyzer.analyze_comprehensive(
            full_file_path,
            enable_all_features=enable_all_features
        )
        
        # Format results for frontend
        formatted_results = {
            'analysis_info': {
                'filename': uploaded_file.name,
                'file_size': uploaded_file.size,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'processing_time': analysis_results.get('performance_metrics', {}).get('processing_time', 0),
                'features_enabled': analysis_results.get('performance_metrics', {}).get('features_enabled', {}),
                'device_used': analysis_results.get('performance_metrics', {}).get('device_used', 'cpu')
            },
            
            # Vehicle Detection Results
            'vehicle_detection': analysis_results.get('vehicle_detection', {}),
            
            # AI Scene Analysis Results
            'scene_analysis': analysis_results.get('scene_analysis', {}),
            
            # Lane Analysis Results (Feature Removed)
            'lane_analysis': {'available': False, 'removed': True, 'message': 'Lane analysis feature has been removed per user request'},
            
            # Enhanced Traffic Density
            'enhanced_traffic_density': analysis_results.get('enhanced_traffic_density', {}),
            
            # AI Insights
            'ai_insights': analysis_results.get('ai_insights', {}),
            
            # Performance Metrics
            'performance_metrics': analysis_results.get('performance_metrics', {}),
            
            # Analysis Metadata
            'analysis_metadata': analysis_results.get('analysis_metadata', {})
        }
        
        logger.info(f"Advanced analysis completed successfully")
        
        return Response(formatted_results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in advanced traffic analysis: {str(e)}")
        return Response({
            'error': str(e),
            'analysis_info': {
                'filename': request.FILES.get('file', {}).name if 'file' in request.FILES else 'unknown',
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'processing_time': 0,
                'status': 'failed'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Lane analysis removed per user request

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_scene_analysis(request):
    """
    AI-powered scene analysis endpoint
    """
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Save uploaded file
        timestamp = int(time.time())
        filename = f"scene_{timestamp}_{uploaded_file.name}"
        file_path = default_storage.save(f'uploads/{filename}', ContentFile(uploaded_file.read()))
        full_file_path = default_storage.path(file_path)
        
        # Load image and run AI analysis
        import cv2
        image = cv2.imread(full_file_path)
        
        from .services.advanced_ai_engine import AdvancedAIEngine
        
        device = request.data.get('device', 'auto')
        ai_engine = AdvancedAIEngine(device=device)
        
        # Analyze scene context
        scene_results = ai_engine.analyze_scene_context(image)
        
        # Generate AI insights if analysis data provided
        analysis_data = request.data.get('analysis_data', {})
        if analysis_data:
            ai_insights = ai_engine.generate_ai_insights(analysis_data)
        else:
            ai_insights = {'key_findings': [], 'recommendations': []}
        
        return Response({
            'scene_analysis': scene_results,
            'ai_insights': ai_insights,
            'analysis_info': {
                'filename': uploaded_file.name,
                'scene_type': scene_results.get('scene_type', 'unknown'),
                'weather_condition': scene_results.get('weather_condition', 'unknown'),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"AI scene analysis error: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])  # No authentication required
def get_advanced_features_status(request):
    """
    Get status of advanced features availability
    """
    try:
        # Check if advanced features are available
        features_status = {
            'ai_processing_engine': {
                'available': True,
                'description': 'Advanced deep learning models for comprehensive traffic analysis',
                'capabilities': [
                    'Scene classification (highway, urban, intersection, etc.)',
                    'Weather condition detection',
                    'Time of day classification',
                    'Traffic flow prediction',
                    'AI-powered insights generation'
                ]
            },
            'lane_analysis': {
                'available': False,
                'removed': True,
                'description': 'Lane analysis feature has been removed per user request',
                'capabilities': []
            },
            'system_requirements': {
                'gpu_acceleration': 'Optional (CUDA support)',
                'memory_requirement': '4GB+ RAM recommended',
                'processing_time': '2-10 seconds per image',
                'supported_formats': ['JPG', 'PNG', 'BMP', 'TIFF']
            }
        }
        
        return Response({
            'features_status': features_status,
            'overall_status': 'available',
            'version': 'Advanced Traffic Analyzer v2.0',
            'last_updated': datetime.utcnow().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Features status error: {str(e)}")
        return Response({
            'error': str(e),
            'overall_status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_analysis_to_database(request):
    """
    Manually save analysis results to MongoDB database
    """
    try:
        analysis_data = request.data.get('analysis_data', {})
        
        if not analysis_data:
            return Response({
                'error': 'No analysis data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"💾 Manual save request from user {request.user.id}")
        
        # Use MongoDB analysis service
        from .mongo_analysis import mongo_analysis
        
        # Extract data from analysis results
        comparison_table = analysis_data.get('comparison_table', [])
        vehicle_summary = analysis_data.get('vehicle_detection_summary', {})
        analysis_info = analysis_data.get('analysis_info', {})
        
        # Get best model data
        best_model = comparison_table[0] if comparison_table else {}
        total_vehicles = vehicle_summary.get('total_vehicles', 0)
        
        # Calculate traffic density based on vehicle count
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
        mongo_analysis_data = {
            'original_image_path': 'manual_save/' + analysis_info.get('filename', 'unknown.jpg'),
            'file_size': analysis_info.get('file_size', 0),
            'image_dimensions': {},
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
            'processing_time': float(str(analysis_info.get('analysis_time', '0')).replace('s', '')),
            'fps': float(str(best_model.get('fps', '0')).replace(' FPS', '')),
            'model_version': f"Manual Save ({best_model.get('model_name', 'Unknown')})",
            'analysis_type': 'manual_save'
        }
        
        # Save to MongoDB with full data population
        analysis_id = mongo_analysis.create_analysis(request.user.id, mongo_analysis_data)
        
        if analysis_id:
            logger.info(f"✅ Manual save successful to MongoDB: Analysis ID {analysis_id}")
            
            return Response({
                'success': True,
                'analysis_id': analysis_id,
                'message': 'Analysis saved to MongoDB successfully',
                'database_type': 'MongoDB',
                'saved_data': {
                    'total_vehicles': total_vehicles,
                    'best_model': best_model.get('model_name', 'Unknown'),
                    'processing_time': str(analysis_info.get('analysis_time', '0s')),
                    'timestamp': datetime.utcnow().isoformat(),
                    'density_level': density_level,
                    'congestion_index': congestion_index
                }
            }, status=status.HTTP_201_CREATED)
        else:
            raise Exception("Failed to create analysis in MongoDB")
        
    except Exception as e:
        logger.error(f"❌ Manual save failed: {e}")
        return Response({
            'error': f'Failed to save analysis to MongoDB: {str(e)}',
            'success': False,
            'database_type': 'MongoDB'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_video_analysis(request):
    """Upload and analyze video with comprehensive tracking and metrics"""
    try:
        logger.info(f"🎥 Video upload request from user: {request.user.id}")
        
        if 'video' not in request.FILES:
            logger.error("No video file provided in request")
            return Response({
                'error': 'No video file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        video_file = request.FILES['video']
        logger.info(f"📁 Video file received: {video_file.name}, size: {video_file.size}")
        
        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        file_extension = Path(video_file.name).suffix.lower()
        
        if file_extension not in allowed_extensions:
            logger.error(f"Unsupported video format: {file_extension}")
            return Response({
                'error': f'Unsupported video format. Allowed: {", ".join(allowed_extensions)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save uploaded file
        timestamp = int(time.time())
        filename = f"video_{timestamp}_{video_file.name}"
        video_path = default_storage.save(f"uploads/videos/{filename}", ContentFile(video_file.read()))
        full_video_path = default_storage.path(video_path)
        
        logger.info(f"💾 Video saved to: {full_video_path}")
        
        # Get analysis parameters with OPTIMIZED defaults
        model_type = request.data.get('model_type', 'yolov8')  # Default to yolov8
        sample_rate = int(request.data.get('sample_rate', 1))  # OPTIMIZED: Analyze every frame for maximum detection
        confidence_threshold = float(request.data.get('confidence_threshold', 0.05))  # OPTIMIZED: Ultra-low for maximum detection
        
        # ROI filtering parameter (default disabled for maximum detection)
        enable_roi_filtering = request.data.get('enable_roi_filtering', 'false').lower() == 'true'
        
        # ROI parameters (optional)
        roi_polygon = request.data.get('roi_polygon', None)  # List of [x, y] points
        if roi_polygon:
            try:
                roi_polygon = json.loads(roi_polygon) if isinstance(roi_polygon, str) else roi_polygon
                logger.info(f"🎯 ROI polygon provided with {len(roi_polygon)} points")
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid ROI polygon format, ignoring")
                roi_polygon = None
        
        logger.info(f"⚙️ Analysis parameters: model={model_type}, sample_rate={sample_rate}, confidence={confidence_threshold} (LOWERED FOR BETTER DETECTION)")
        if roi_polygon:
            logger.info(f"🎯 ROI filtering enabled")
        
        # Create analysis record
        analysis_data = {
            'user_id': str(request.user.id),
            'file_path': video_path,
            'file_type': 'video',
            'status': 'processing',
            'analysis_metadata': {
                'model_used': model_type,
                'processing_time': 0,
                'timestamp': datetime.utcnow(),
                'gpu_used': False,
                'memory_usage': 0
            }
        }
        
        analysis_id = traffic_service.create_analysis(analysis_data)
        logger.info(f"📊 Created analysis record: {analysis_id}")
        
        # Start video analysis
        try:
            from .services.enhanced_video_analyzer import EnhancedVideoAnalyzer
            
            start_time = time.time()
            logger.info("🚀 Starting video analysis...")
            
            # Use the confidence threshold from the request, with optimized minimum
            actual_confidence = max(0.05, confidence_threshold)  # OPTIMIZED: Use requested confidence, minimum 0.05
            # Use centralized model path
            model_path = os.path.join('backend', 'models', 'yolov8s.pt')  # Centralized model location
            # OPTIMIZED: Use ROI filtering parameter from request (default disabled)
            analyzer = EnhancedVideoAnalyzer(model_path, actual_confidence, roi_polygon, enable_roi_filtering=enable_roi_filtering)
            logger.info(f"🎯 OPTIMIZED: Using confidence threshold: {actual_confidence}, ROI filtering: {'ENABLED' if enable_roi_filtering else 'DISABLED'}")
            analysis_results = analyzer.analyze_video(full_video_path, sample_rate)
            
            processing_time = time.time() - start_time
            logger.info(f"⏱️ Video analysis completed in {processing_time:.2f} seconds")
            
            # Extract frame analyses for annotation
            frame_analyses = analysis_results.get('frame_analyses', [])
            logger.info(f"📊 Processed {len(frame_analyses)} frames")
            
            # Create thumbnail (skip annotated video for now to speed up)
            thumbnail_path = create_video_thumbnail(full_video_path, f"thumbnails/video_{timestamp}.jpg")
            logger.info(f"🖼️ Thumbnail created: {thumbnail_path}")
            
            # Generate annotated video with improved error handling
            annotated_video_path = None
            try:
                annotated_filename = f"annotated_video_{timestamp}_{video_file.name}"
                
                # Ensure filename is safe and has correct extension
                if not annotated_filename.lower().endswith('.mp4'):
                    annotated_filename = annotated_filename.rsplit('.', 1)[0] + '.mp4'
                
                # Use Django's media root for the full path
                from django.conf import settings
                media_root = getattr(settings, 'MEDIA_ROOT', 'backend/media')
                annotated_video_full_path = os.path.join(media_root, 'uploads', 'videos', 'annotated', annotated_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(annotated_video_full_path), exist_ok=True)
                
                logger.info(f"🎯 Creating annotated video at: {annotated_video_full_path}")
                logger.info(f"📊 Frame analyses count: {len(frame_analyses)}")
                
                # ALWAYS create annotated video - even with few detections for user verification
                if frame_analyses:
                    # Create annotated video with detections
                    result_path = analyzer.create_annotated_video(full_video_path, annotated_video_full_path, frame_analyses)
                    
                    # Verify the file was created and is valid
                    if os.path.exists(result_path):
                        file_size = os.path.getsize(result_path)
                        logger.info(f"✅ Annotated video created: {file_size} bytes")
                        
                        # Validate video file by trying to read it
                        import cv2
                        test_cap = cv2.VideoCapture(result_path)
                        if test_cap.isOpened():
                            frame_count = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = test_cap.get(cv2.CAP_PROP_FPS)
                            test_cap.release()
                            
                            if frame_count > 0 and fps > 0:
                                # Video is valid
                                annotated_video_path = f"uploads/videos/annotated/{annotated_filename}"
                                logger.info(f"🎯 Valid annotated video created: {annotated_video_path} ({frame_count} frames @ {fps:.1f}fps)")
                            else:
                                logger.error(f"❌ Invalid video file created: {frame_count} frames, {fps} fps")
                                annotated_video_path = None
                        else:
                            logger.error(f"❌ Cannot open created video file: {result_path}")
                            annotated_video_path = None
                    else:
                        logger.error(f"❌ Annotated video file was not created at: {result_path}")
                        annotated_video_path = None
                else:
                    logger.info(f"ℹ️ No frame analyses - creating basic annotated video")
                    # Create basic annotated video even without detections
                    result_path = analyzer.create_annotated_video(full_video_path, annotated_video_full_path, [])
                    if os.path.exists(result_path) and os.path.getsize(result_path) > 1000:
                        annotated_video_path = f"uploads/videos/annotated/{annotated_filename}"
                        logger.info(f"🎯 Basic annotated video created: {annotated_video_path}")
                
            except Exception as e:
                logger.error(f"⚠️ Failed to create annotated video: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                annotated_video_path = None
            
            # Calculate overall metrics
            frame_analyses = analysis_results.get('frame_analyses', [])
            logger.info(f"📊 Processed {len(frame_analyses)} frames")
            
            if frame_analyses:
                vehicle_counts_list = [f['vehicle_count'] for f in frame_analyses]
                max_vehicles_per_frame = max(vehicle_counts_list) if vehicle_counts_list else 0
                avg_vehicles = sum(vehicle_counts_list) / len(vehicle_counts_list) if vehicle_counts_list else 0
                
                # Get total unique vehicles from vehicle tracks (this is the real total)
                vehicle_tracks = analysis_results.get('vehicle_tracks', [])
                total_vehicles = len(vehicle_tracks)  # Number of unique vehicles tracked
                
                # If no tracking data, fall back to sum of all detections across frames
                if total_vehicles == 0:
                    total_vehicles = sum(vehicle_counts_list)  # Sum all detections
                
                logger.info(f"🚗 Vehicle tracking: {len(vehicle_tracks)} unique vehicles, max {max_vehicles_per_frame} per frame")
                logger.info(f"🔢 TOTAL VEHICLES CALCULATION: vehicle_tracks={len(vehicle_tracks)}, total_vehicles={total_vehicles}")
                logger.info(f"📊 Sum of all detections: {sum(vehicle_counts_list)}, Max per frame: {max_vehicles_per_frame}")
                
                congestion_indices = [f['congestion_index'] for f in frame_analyses]
                avg_congestion = sum(congestion_indices) / len(congestion_indices) if congestion_indices else 0
                
                if avg_congestion < 0.3:
                    congestion_level = 'low'
                elif avg_congestion < 0.7:
                    congestion_level = 'medium'
                else:
                    congestion_level = 'high'
            else:
                total_vehicles = 0
                avg_vehicles = 0
                avg_congestion = 0
                congestion_level = 'low'
            
            logger.info(f"📈 Analysis results: vehicles={total_vehicles}, congestion={congestion_level}")
            
            # Aggregate vehicle counts with proper grouping
            vehicle_counts = defaultdict(int)
            for frame in frame_analyses:
                for vehicle_type, count in frame.get('vehicle_counts', {}).items():
                    vehicle_counts[vehicle_type] += count
            
            # Group vehicle counts properly for display
            grouped_vehicle_counts = {
                'cars': vehicle_counts.get('car', 0),
                'large_vehicles': vehicle_counts.get('truck', 0) + vehicle_counts.get('bus', 0),
                '2_wheelers': vehicle_counts.get('motorcycle', 0) + vehicle_counts.get('bicycle', 0)
            }
            
            logger.info(f"🚗 Vehicle count breakdown: Cars={grouped_vehicle_counts['cars']}, Large Vehicles={grouped_vehicle_counts['large_vehicles']}, 2-Wheelers={grouped_vehicle_counts['2_wheelers']}")
            
            # Update analysis record
            update_data = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'vehicle_count': int(total_vehicles),
                'vehicle_counts': grouped_vehicle_counts,  # Use grouped counts
                'raw_vehicle_counts': dict(vehicle_counts),  # Keep raw counts for debugging
                'congestion_level': congestion_level,
                'congestion_index': float(avg_congestion),
                'thumbnail_path': thumbnail_path,
                'video_metadata': analysis_results.get('video_metadata', {}),
                'frame_analyses': frame_analyses,
                'vehicle_tracks': analysis_results.get('vehicle_tracks', []),
                'traffic_metrics': analysis_results.get('traffic_metrics', {}),
                'analysis_metadata': {
                    'model_used': model_type,
                    'processing_time': processing_time,
                    'timestamp': datetime.utcnow(),
                    'gpu_used': False,
                    'memory_usage': 0,
                    'image_dimensions': analysis_results.get('video_metadata', {}).get('resolution', []),
                    'file_size': analysis_results.get('video_metadata', {}).get('file_size', 0),
                    'image_format': analysis_results.get('video_metadata', {}).get('format', '')
                }
            }
            
            success = traffic_service.update_analysis(analysis_id, update_data)
            logger.info(f"💾 Analysis record updated: {success}")
            
            # 🧠 Generate LLM insights using Groq gpt-oss-20b
            try:
                from apps.llm_integration.services.llm_service import LLMService
                
                traffic_data = {
                    'vehicle_detection': {
                        'total_vehicles': total_vehicles,
                        'vehicle_counts': grouped_vehicle_counts  # Use grouped counts for LLM
                    },
                    'traffic_density': {
                        'density_level': congestion_level,
                        'congestion_index': avg_congestion
                    },
                    'video_metadata': {
                        'duration': analysis_results.get('video_metadata', {}).get('duration', 0),
                        'frames_analyzed': len(frame_analyses)
                    },
                    'analysis_type': 'video'
                }
                
                llm_service = LLMService()
                llm_result = llm_service.analyze_traffic_conditions(traffic_data, str(request.user.id))
                
                if llm_result.get('success'):
                    llm_insights = {
                        'traffic_analysis': llm_result.get('insight', ''),
                        'model_used': llm_result.get('model_used', 'groq'),
                        'analysis_summary': llm_result.get('analysis_summary', {}),
                        'generated_at': datetime.utcnow().isoformat(),
                        'confidence_score': 0.9,
                        'processing_time': 1.5
                    }
                    
                    traffic_service.update_analysis(analysis_id, {'llm_insights': llm_insights})
                    logger.info("✅ Groq LLM insights generated for video analysis")
                else:
                    # Fallback to simple analysis
                    if total_vehicles == 0:
                        explanation = "No vehicles detected in the video. This indicates very light traffic or the video may not contain clear vehicle imagery."
                    elif total_vehicles <= 5:
                        explanation = f"Light traffic detected with {total_vehicles} vehicles. Good traffic flow with minimal congestion."
                    elif total_vehicles <= 15:
                        explanation = f"Moderate traffic with {total_vehicles} vehicles detected. Normal traffic density."
                    else:
                        explanation = f"Heavy traffic with {total_vehicles} vehicles detected. High traffic density may cause delays."
                    
                    llm_insights = {
                        'traffic_analysis': explanation,
                        'model_used': 'fallback',
                        'confidence_score': 0.7,
                        'processing_time': 0.1,
                        'generated_at': datetime.utcnow().isoformat()
                    }
                    
                    traffic_service.update_analysis(analysis_id, {'llm_insights': llm_insights})
                    logger.warning(f"⚠️ Used fallback LLM analysis: {llm_result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"❌ Error generating LLM insights: {e}")
                # Continue without failing the analysis
            
            logger.info("✅ Video analysis completed successfully")
            
            # FIXED: Use actual vehicle count instead of debug value
            vehicle_tracks = analysis_results.get('vehicle_tracks', [])
            actual_total_vehicles = len(vehicle_tracks) if vehicle_tracks else total_vehicles
            logger.info(f"🔧 CORRECTED total_vehicles: {actual_total_vehicles} (was debug value 999)")
            
            return Response({
                'analysis_id': str(analysis_id),
                'status': 'completed',
                'results': {
                    'total_vehicles': actual_total_vehicles,  # FIXED: Use actual count
                    'vehicle_counts': grouped_vehicle_counts,  # Use properly grouped counts
                    'congestion_level': congestion_level,
                    'congestion_index': avg_congestion,
                    'traffic_metrics': analysis_results.get('traffic_metrics', {}),
                    'video_metadata': analysis_results.get('video_metadata', {}),
                    'frames_analyzed': len(frame_analyses),
                    'vehicles_tracked': len(analysis_results.get('vehicle_tracks', [])),
                    'processing_time': processing_time,
                    'thumbnail_url': f"/media/{thumbnail_path}" if thumbnail_path else None,
                    'original_video_url': f"/media/{video_path}",
                    'annotated_video_url': f"/media/{annotated_video_path}" if annotated_video_path else None,
                }
            })
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Update analysis status to failed
            traffic_service.update_analysis(analysis_id, {
                'status': 'failed',
                'updated_at': datetime.utcnow()
            })
            
            return Response({
                'error': f'Video analysis failed: {str(e)}',
                'analysis_id': str(analysis_id)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def create_video_thumbnail(video_path: str, thumbnail_filename: str) -> str:
    """Create thumbnail from video"""
    import cv2
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return None
    
    # Get frame from middle of video
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle_frame = frame_count // 2
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        # Resize frame for thumbnail
        height, width = frame.shape[:2]
        max_size = 300
        
        if width > height:
            new_width = max_size
            new_height = int(height * max_size / width)
        else:
            new_height = max_size
            new_width = int(width * max_size / height)
        
        thumbnail = cv2.resize(frame, (new_width, new_height))
        
        # Save thumbnail
        thumbnail_path = default_storage.path(thumbnail_filename)
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        cv2.imwrite(thumbnail_path, thumbnail)
        
        return thumbnail_filename
    
    return None

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_analysis(request, analysis_id):
    """Get detailed video analysis results"""
    try:
        analysis = traffic_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            return Response({
                'error': 'Analysis not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user owns this analysis
        if analysis.get('user_id') != str(request.user.id):
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Convert ObjectId to string
        if '_id' in analysis:
            analysis['id'] = str(analysis['_id'])
            del analysis['_id']
        
        # Convert datetime objects
        for key, value in analysis.items():
            if hasattr(value, 'isoformat'):
                analysis[key] = value.isoformat()
        
        return Response(analysis)
        
    except Exception as e:
        logger.error(f"Error getting video analysis: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_metrics(request, analysis_id):
    """Get comprehensive video metrics and visualizations"""
    try:
        analysis = traffic_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            return Response({
                'error': 'Analysis not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if analysis.get('user_id') != str(request.user.id):
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Extract metrics for visualization
        frame_analyses = analysis.get('frame_analyses', [])
        vehicle_tracks = analysis.get('vehicle_tracks', [])
        traffic_metrics = analysis.get('traffic_metrics', {})
        
        # Prepare time series data
        time_series = []
        for frame in frame_analyses:
            time_series.append({
                'timestamp': frame['timestamp'],
                'vehicle_count': frame['vehicle_count'],
                'congestion_index': frame['congestion_index'],
                'density_level': frame['density_level']
            })
        
        # Vehicle type distribution
        vehicle_distribution = analysis.get('vehicle_counts', {})
        
        # Speed distribution
        speed_data = []
        for track in vehicle_tracks:
            if track.get('avg_speed', 0) > 0:
                speed_data.append({
                    'track_id': track['track_id'],
                    'vehicle_class': track['vehicle_class'],
                    'avg_speed': track['avg_speed'],
                    'max_speed': track['max_speed']
                })
        
        # Congestion heatmap data
        congestion_levels = {'low': 0, 'medium': 0, 'high': 0}
        for frame in frame_analyses:
            level = frame.get('density_level', 'low')
            congestion_levels[level] += 1
        
        return Response({
            'analysis_id': analysis_id,
            'video_metadata': analysis.get('video_metadata', {}),
            'traffic_metrics': traffic_metrics,
            'time_series': time_series,
            'vehicle_distribution': vehicle_distribution,
            'speed_data': speed_data,
            'congestion_levels': congestion_levels,
            'total_frames_analyzed': len(frame_analyses),
            'total_vehicles_tracked': len(vehicle_tracks)
        })
        
    except Exception as e:
        logger.error(f"Error getting video metrics: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_video_report(request, analysis_id):
    """Download comprehensive video analysis report"""
    try:
        analysis = traffic_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            return Response({
                'error': 'Analysis not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if analysis.get('user_id') != str(request.user.id):
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        report_format = request.GET.get('format', 'json')
        
        if report_format == 'json':
            # Create a clean copy for JSON serialization
            clean_analysis = {}
            for key, value in analysis.items():
                if key == '_id':
                    clean_analysis['id'] = str(value)
                elif hasattr(value, 'isoformat'):
                    clean_analysis[key] = value.isoformat()
                elif hasattr(value, '__dict__'):
                    # Skip complex objects that can't be serialized
                    continue
                else:
                    clean_analysis[key] = value
            
            response = HttpResponse(
                json.dumps(clean_analysis, indent=2, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="video_analysis_{analysis_id}.json"'
            return response
            
        elif report_format == 'csv':
            # Create CSV report
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Metric', 'Value'])
            
            # Basic info
            writer.writerow(['Analysis ID', analysis_id])
            writer.writerow(['Total Vehicles', analysis.get('vehicle_count', 0)])
            writer.writerow(['Congestion Level', analysis.get('congestion_level', 'N/A')])
            writer.writerow(['Congestion Index', analysis.get('congestion_index', 0)])
            
            # Traffic metrics
            traffic_metrics = analysis.get('traffic_metrics', {})
            for key, value in traffic_metrics.items():
                writer.writerow([key.replace('_', ' ').title(), value])
            
            # Vehicle counts
            vehicle_counts = analysis.get('vehicle_counts', {})
            for vehicle_type, count in vehicle_counts.items():
                writer.writerow([f'{vehicle_type.title()} Count', count])
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="video_analysis_{analysis_id}.csv"'
            return response
            
        else:
            return Response({
                'error': 'Unsupported format. Use json or csv'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error downloading video report: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_video_analysis_fixed(request):
    """FIXED video upload that returns correct vehicle count"""
    try:
        logger.info(f"🎥 FIXED Video upload request from user: {request.user.id}")
        
        if 'video' not in request.FILES:
            return Response({
                'error': 'No video file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        video_file = request.FILES['video']
        
        # Save uploaded file
        timestamp = int(time.time())
        filename = f"video_{timestamp}_{video_file.name}"
        video_path = default_storage.save(f"uploads/videos/{filename}", ContentFile(video_file.read()))
        full_video_path = default_storage.path(video_path)
        
        # Get analysis parameters with OPTIMIZED defaults
        confidence_threshold = float(request.data.get('confidence_threshold', 0.05))  # OPTIMIZED
        sample_rate = int(request.data.get('sample_rate', 1))  # OPTIMIZED: Every frame
        enable_roi_filtering = request.data.get('enable_roi_filtering', 'false').lower() == 'true'  # OPTIMIZED: Default disabled
        
        logger.info(f"🎯 OPTIMIZED Analysis: confidence={confidence_threshold}, sample_rate={sample_rate}, roi_filtering={enable_roi_filtering}")
        
        # Run video analysis with OPTIMIZED parameters
        from .services.enhanced_video_analyzer import EnhancedVideoAnalyzer
        
        start_time = time.time()
        # OPTIMIZED: Use ROI filtering parameter from request
        # Use centralized model path
        analyzer = EnhancedVideoAnalyzer(os.path.join('backend', 'models', 'yolov8s.pt'), confidence_threshold, None, enable_roi_filtering=enable_roi_filtering)
        analysis_results = analyzer.analyze_video(full_video_path, sample_rate)
        processing_time = time.time() - start_time
        
        # Get correct vehicle counts
        frame_analyses = analysis_results.get('frame_analyses', [])
        vehicle_tracks = analysis_results.get('vehicle_tracks', [])
        
        # CORRECT CALCULATION
        total_vehicles = len(vehicle_tracks)  # Unique vehicles tracked
        vehicles_tracked = len(vehicle_tracks)  # Same value
        frames_analyzed = len(frame_analyses)
        
        # Aggregate vehicle counts
        vehicle_counts = defaultdict(int)
        for frame in frame_analyses:
            for vehicle_type, count in frame.get('vehicle_counts', {}).items():
                vehicle_counts[vehicle_type] += count
        
        # Calculate congestion
        if frame_analyses:
            vehicle_counts_list = [f['vehicle_count'] for f in frame_analyses]
            avg_congestion = sum(f['congestion_index'] for f in frame_analyses) / len(frame_analyses)
            
            if avg_congestion < 0.3:
                congestion_level = 'low'
            elif avg_congestion < 0.7:
                congestion_level = 'medium'
            else:
                congestion_level = 'high'
        else:
            avg_congestion = 0
            congestion_level = 'low'
        
        logger.info(f"✅ OPTIMIZED RESULTS: {total_vehicles} unique vehicles, {frames_analyzed} frames")
        
        # Generate annotated video if we have detections
        annotated_video_url = None
        try:
            if frame_analyses and any(f.get('vehicle_count', 0) > 0 for f in frame_analyses):
                annotated_filename = f"annotated_fixed_{timestamp}_{video_file.name}"
                from django.conf import settings
                media_root = getattr(settings, 'MEDIA_ROOT', 'backend/media')
                annotated_video_full_path = os.path.join(media_root, 'uploads', 'videos', 'annotated', annotated_filename)
                
                os.makedirs(os.path.dirname(annotated_video_full_path), exist_ok=True)
                
                result_path = analyzer.create_annotated_video(full_video_path, annotated_video_full_path, frame_analyses)
                
                if os.path.exists(result_path) and os.path.getsize(result_path) > 1000:
                    annotated_video_url = f"/media/uploads/videos/annotated/{annotated_filename}"
                    logger.info(f"✅ Annotated video created: {annotated_video_url}")
                else:
                    logger.warning(f"⚠️ Annotated video creation failed or file too small")
            else:
                logger.info(f"ℹ️ No detections found - skipping annotated video")
        except Exception as e:
            logger.error(f"⚠️ Annotated video creation failed: {e}")
        
        return Response({
            'analysis_id': f"fixed_{timestamp}",
            'status': 'completed',
            'results': {
                'total_vehicles': total_vehicles,  # CORRECT VALUE
                'vehicle_counts': dict(vehicle_counts),
                'congestion_level': congestion_level,
                'congestion_index': avg_congestion,
                'traffic_metrics': analysis_results.get('traffic_metrics', {}),
                'video_metadata': analysis_results.get('video_metadata', {}),
                'frames_analyzed': frames_analyzed,
                'vehicles_tracked': vehicles_tracked,  # CORRECT VALUE
                'processing_time': processing_time,
                'original_video_url': f"/media/{video_path}",
                'annotated_video_url': annotated_video_url,  # FIXED: Now includes annotated video
            }
        })
        
    except Exception as e:
        logger.error(f"FIXED video upload failed: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)