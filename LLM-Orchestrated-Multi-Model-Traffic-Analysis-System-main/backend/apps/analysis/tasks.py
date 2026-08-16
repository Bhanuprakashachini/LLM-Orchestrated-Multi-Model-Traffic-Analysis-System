"""
Celery tasks for background processing - MongoDB compatible
"""
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]
users = db.users
analysis_results = db.analysis_results
video_analyses = db.video_analyses
frame_analyses = db.frame_analyses
model_performance = db.model_performance

# Try to import celery, make it optional for development
try:
    from celery import shared_task
except ImportError:
    # Mock shared_task decorator for development without celery
    def shared_task(func):
        return func


@shared_task
def analyze_image_task(image_path, user_id):
    """
    Background task for image analysis
    """
    try:
        # Import here to avoid circular imports
        from .services.yolov12_analyzer import YOLOv12TrafficAnalyzer
        
        # Initialize analyzer
        analyzer = YOLOv12TrafficAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_traffic_scene(image_path)
        
        # Save results to MongoDB
        analysis_data = {
            'user_id': str(user_id),
            'original_image': image_path,
            'vehicle_detection': result.get('vehicle_detection', {}),
            'scene_classification': result.get('scene_classification', {}),
            'traffic_density': result.get('traffic_density', {}),
            'traffic_flow': result.get('traffic_flow', {}),
            'processing_time': result.get('processing_time', 0.0),
            'fps': result.get('fps', 0.0),
            'model_version': 'YOLOv12',
            'analysis_type': 'image',
            'status': 'completed',
            'success': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = analysis_results.insert_one(analysis_data)
        analysis_id = str(result.inserted_id)
        
        logger.info(f"Image analysis completed for user {user_id}: {analysis_id}")
        return analysis_id
        
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise


@shared_task
def analyze_video_task(video_path, user_id, session_id):
    """
    Background task for video analysis
    """
    try:
        # Import here to avoid circular imports
        from .services.yolov12_analyzer import YOLOv12TrafficAnalyzer
        
        # Initialize analyzer
        analyzer = YOLOv12TrafficAnalyzer()
        
        # Get video analysis session from MongoDB
        video_analysis = video_analyses.find_one({
            'session_id': session_id,
            'user_id': str(user_id)
        })
        
        if not video_analysis:
            raise Exception(f"Video analysis session not found: {session_id}")
        
        # Process video frames
        frame_results = analyzer.analyze_video(video_path)
        
        # Save frame results to MongoDB
        for frame_data in frame_results:
            frame_doc = {
                'video_analysis_id': str(video_analysis['_id']),
                'session_id': session_id,
                'frame_number': frame_data['frame_number'],
                'vehicle_detection': frame_data.get('vehicle_detection', {}),
                'scene_classification': frame_data.get('scene_classification', {}),
                'traffic_density': frame_data.get('traffic_density', {}),
                'traffic_flow': frame_data.get('traffic_flow', {}),
                'processing_time': frame_data.get('processing_time', 0.0),
                'timestamp': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            frame_analyses.insert_one(frame_doc)
        
        # Update video analysis statistics
        video_analyses.update_one(
            {'_id': video_analysis['_id']},
            {
                '$set': {
                    'total_frames_processed': len(frame_results),
                    'status': 'completed',
                    'end_time': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Video analysis completed for session {session_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Video analysis failed: {str(e)}")
        raise


@shared_task
def cleanup_old_files():
    """
    Cleanup old analysis files
    """
    try:
        import os
        from datetime import datetime, timedelta
        from django.conf import settings
        
        # Delete analysis results older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_analyses = analysis_results.find({'created_at': {'$lt': cutoff_date}})
        
        deleted_count = 0
        for analysis in old_analyses:
            # Delete associated files
            if analysis.get('original_image') and os.path.exists(analysis['original_image']):
                os.remove(analysis['original_image'])
            if analysis.get('annotated_image') and os.path.exists(analysis['annotated_image']):
                os.remove(analysis['annotated_image'])
            
            # Delete database record
            analysis_results.delete_one({'_id': analysis['_id']})
            deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old analysis records")
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise


@shared_task
def generate_performance_report():
    """
    Generate daily performance report
    """
    try:
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Get today's analyses from MongoDB
        today_analyses = list(analysis_results.find({
            'created_at': {'$gte': start_of_day, '$lte': end_of_day}
        }))
        
        if today_analyses:
            # Calculate metrics
            processing_times = [a.get('processing_time', 0) for a in today_analyses if a.get('processing_time')]
            fps_values = [a.get('fps', 0) for a in today_analyses if a.get('fps')]
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0.0
            total_analyses = len(today_analyses)
            
            # Create performance record in MongoDB
            performance_data = {
                'model_name': 'YOLOv12',
                'version': '1.0',
                'date': today,
                'total_analyses': total_analyses,
                'average_processing_time': avg_processing_time,
                'average_fps': avg_fps,
                'device': 'cpu',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Update or insert performance record
            model_performance.update_one(
                {
                    'model_name': 'YOLOv12',
                    'version': '1.0',
                    'date': today
                },
                {'$set': performance_data},
                upsert=True
            )
            
            logger.info(f"Performance report generated for {today}")
        
    except Exception as e:
        logger.error(f"Performance report generation failed: {str(e)}")
        raise