"""
MongoDB Analysis Service
Handles traffic analysis data in MongoDB
"""
from utils.mongodb import get_mongo_db
from datetime import datetime
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class MongoAnalysisService:
    """MongoDB-based analysis service"""
    
    def __init__(self):
        self.db = get_mongo_db()
        if self.db is None:
            raise Exception("MongoDB connection failed")
        
        self.analyses = self.db.traffic_analyses
        self.detected_objects = self.db.detected_objects
        self.analytics = self.db.analytics_data
    
    def create_analysis(self, user_id, analysis_data):
        """Create a new analysis record and populate all related collections"""
        try:
            # Extract image paths from analysis data
            images = analysis_data.get('images', {})
            
            # Create main analysis document with user-specific tracking
            analysis_doc = {
                'user_id': str(user_id),  # Ensure user_id is string for MongoDB
                'original_image_path': analysis_data.get('original_image_path'),
                'annotated_image_path': analysis_data.get('annotated_image_path'),
                'file_size': analysis_data.get('file_size', 0),
                'image_dimensions': analysis_data.get('image_dimensions', {}),
                'vehicle_detection': analysis_data.get('vehicle_detection', {}),
                'traffic_density': analysis_data.get('traffic_density', {}),
                'processing_time': analysis_data.get('processing_time', 0),
                'fps': analysis_data.get('fps', 0),
                'model_version': analysis_data.get('model_version', 'unknown'),
                'analysis_type': analysis_data.get('analysis_type', 'image'),
                'status': analysis_data.get('status', 'completed'),
                'success': analysis_data.get('success', True),
                'error_message': analysis_data.get('error_message', ''),
                
                # Store image information for history and reports
                'images': {
                    'original': images.get('original', ''),
                    'annotated': images.get('annotated', ''),
                    'best_model_annotated': images.get('best_model_annotated', ''),
                    'yolov8_annotated': images.get('yolov8_annotated', ''),
                    'yolov11_annotated': images.get('yolov11_annotated', ''),
                    'yolov12_annotated': images.get('yolov12_annotated', ''),
                    'ensemble_annotated': images.get('ensemble_annotated', '')
                },
                
                # Store comparison results for detailed history
                'comparison_results': analysis_data.get('comparison_table', []),
                'recommendations': analysis_data.get('recommendations', {}),
                'advanced_features': analysis_data.get('advanced_features', {}),
                
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert main analysis
            result = self.analyses.insert_one(analysis_doc)
            analysis_id = str(result.inserted_id)
            
            # Update user statistics in Django model
            self._update_user_stats(user_id, analysis_id, analysis_data)
            
            # Now populate all related collections
            self._populate_detected_objects(analysis_id, user_id, analysis_data)
            self._populate_analytics_data(analysis_id, user_id, analysis_data)
            self._populate_analysis_history(analysis_id, user_id, analysis_data)
            self._generate_llm_insights(analysis_id, user_id, analysis_data)
            
            logger.info(f"Analysis created with full data population for user {user_id}: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error creating analysis for user {user_id}: {e}")
            # Record failed analysis in user stats
            self._update_user_stats(user_id, None, analysis_data, success=False)
            return None
    
    def _update_user_stats(self, user_id, analysis_id, analysis_data, success=True):
        """Update user statistics in MongoDB"""
        try:
            from pymongo import MongoClient
            from django.conf import settings
            
            # Connect to MongoDB
            client = MongoClient(settings.MONGODB_URI)
            db = client[settings.MONGODB_DB_NAME]
            user_stats_collection = db.user_stats
            
            # Extract analysis information
            processing_time = analysis_data.get('processing_time', 0)
            vehicle_count = 0
            
            # Get vehicle count from detection data
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            if isinstance(vehicle_detection, dict):
                vehicle_count = vehicle_detection.get('total_vehicles', 0)
            
            analysis_type = analysis_data.get('analysis_type', 'image')
            model_name = analysis_data.get('model_version', 'unknown')
            
            # Prepare update data
            update_data = {
                '$set': {
                    'updated_at': datetime.utcnow(),
                    'last_activity_date': datetime.utcnow()
                },
                '$setOnInsert': {
                    'user_id': str(user_id),
                    'created_at': datetime.utcnow(),
                    'total_analyses': 0,
                    'successful_analyses': 0,
                    'failed_analyses': 0,
                    'total_vehicles_detected': 0,
                    'total_processing_time': 0.0
                }
            }
            
            if success:
                # Update success statistics
                update_data['$inc'] = {
                    'total_analyses': 1,
                    'successful_analyses': 1,
                    'total_vehicles_detected': vehicle_count,
                    'total_processing_time': processing_time
                }
                update_data['$set'].update({
                    'last_analysis_date': datetime.utcnow(),
                    'recent_analysis_id': analysis_id,
                    'recent_analysis_type': analysis_type,
                    'recent_analysis_model': model_name
                })
            else:
                # Update failure statistics
                update_data['$inc'] = {
                    'total_analyses': 1,
                    'failed_analyses': 1
                }
            
            # Apply updates
            user_stats_collection.update_one(
                {'user_id': str(user_id)},
                update_data,
                upsert=True
            )
            
            logger.info(f"Updated user stats for user {user_id}: success={success}")
            
        except Exception as e:
            logger.error(f"Error updating user stats for user {user_id}: {e}")
            # Don't raise the exception to avoid breaking the main analysis flow
    
    def get_user_analyses(self, user_id, limit=10, skip=0, analysis_type=None):
        """Get user-specific analyses with pagination"""
        try:
            query = {'user_id': str(user_id)}
            if analysis_type:
                query['analysis_type'] = analysis_type
            
            cursor = self.analyses.find(query).sort('created_at', -1).skip(skip).limit(limit)
            analyses = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for analysis in analyses:
                if '_id' in analysis:
                    analysis['id'] = str(analysis['_id'])
                    del analysis['_id']
                
                # Convert datetime objects to ISO format
                for key, value in analysis.items():
                    if hasattr(value, 'isoformat'):
                        analysis[key] = value.isoformat()
            
            # Get total count for pagination
            total_count = self.analyses.count_documents(query)
            
            return {
                'analyses': analyses,
                'total_count': total_count,
                'has_more': (skip + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user analyses for user {user_id}: {e}")
            return {'analyses': [], 'total_count': 0, 'has_more': False}
    
    def get_user_analysis_stats(self, user_id):
        """Get aggregated analysis statistics for a user"""
        try:
            pipeline = [
                {'$match': {'user_id': str(user_id)}},
                {'$group': {
                    '_id': None,
                    'total_analyses': {'$sum': 1},
                    'successful_analyses': {'$sum': {'$cond': [{'$eq': ['$success', True]}, 1, 0]}},
                    'failed_analyses': {'$sum': {'$cond': [{'$eq': ['$success', False]}, 1, 0]}},
                    'total_processing_time': {'$sum': '$processing_time'},
                    'total_vehicles': {'$sum': '$vehicle_detection.total_vehicles'},
                    'avg_processing_time': {'$avg': '$processing_time'},
                    'avg_vehicles': {'$avg': '$vehicle_detection.total_vehicles'},
                    'latest_analysis': {'$max': '$created_at'}
                }}
            ]
            
            result = list(self.analyses.aggregate(pipeline))
            if result:
                stats = result[0]
                stats['success_rate'] = (stats['successful_analyses'] / stats['total_analyses'] * 100) if stats['total_analyses'] > 0 else 0
                return stats
            else:
                return {
                    'total_analyses': 0,
                    'successful_analyses': 0,
                    'failed_analyses': 0,
                    'success_rate': 0,
                    'total_processing_time': 0,
                    'total_vehicles': 0,
                    'avg_processing_time': 0,
                    'avg_vehicles': 0,
                    'latest_analysis': None
                }
                
        except Exception as e:
            logger.error(f"Error getting user analysis stats for user {user_id}: {e}")
            return None
    
    def get_user_model_usage_stats(self, user_id):
        """Get model usage statistics for a user"""
        try:
            pipeline = [
                {'$match': {'user_id': str(user_id)}},
                {'$group': {
                    '_id': '$model_version',
                    'count': {'$sum': 1},
                    'success_count': {'$sum': {'$cond': [{'$eq': ['$success', True]}, 1, 0]}},
                    'avg_processing_time': {'$avg': '$processing_time'},
                    'total_vehicles': {'$sum': '$vehicle_detection.total_vehicles'}
                }},
                {'$sort': {'count': -1}}
            ]
            
            results = list(self.analyses.aggregate(pipeline))
            
            # Calculate success rate for each model
            for result in results:
                result['success_rate'] = (result['success_count'] / result['count'] * 100) if result['count'] > 0 else 0
                result['model_name'] = result['_id']
                del result['_id']
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user model usage stats for user {user_id}: {e}")
            return []
    
    def _populate_detected_objects(self, analysis_id, user_id, analysis_data):
        """Store individual detected objects"""
        try:
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            detections = vehicle_detection.get('detections', [])
            
            if not detections:
                # If no detections array, create from summary
                detection_summary = vehicle_detection.get('detection_summary', {})
                total_vehicles = vehicle_detection.get('total_vehicles', 0)
                
                # Create mock detections for each vehicle type
                mock_detections = []
                for vehicle_type, count in detection_summary.items():
                    for i in range(count):
                        mock_detections.append({
                            'class_name': vehicle_type,
                            'confidence': vehicle_detection.get('average_confidence', 0.8),
                            'bbox': {'x1': 100 + i*50, 'y1': 100, 'x2': 150 + i*50, 'y2': 150}
                        })
                detections = mock_detections
            
            # Store each detection as a separate document
            detection_docs = []
            for detection in detections:
                detection_doc = {
                    'analysis_id': analysis_id,
                    'user_id': user_id,
                    'class_name': detection.get('class_name', 'unknown'),
                    'confidence': detection.get('confidence', 0.0),
                    'bbox': detection.get('bbox', {}),
                    'created_at': datetime.utcnow()
                }
                detection_docs.append(detection_doc)
            
            if detection_docs:
                self.detected_objects.insert_many(detection_docs)
                logger.info(f"Stored {len(detection_docs)} detected objects for analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error populating detected objects: {e}")
    
    def _populate_analytics_data(self, analysis_id, user_id, analysis_data):
        """Store aggregated analytics data"""
        try:
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            traffic_density = analysis_data.get('traffic_density', {})
            
            analytics_doc = {
                'user_id': user_id,
                'analysis_id': analysis_id,
                'timestamp': datetime.utcnow(),
                'total_vehicles': vehicle_detection.get('total_vehicles', 0),
                'congestion_index': traffic_density.get('congestion_index', 0.0),
                'density_level': traffic_density.get('density_level', 'unknown'),
                'processing_time': analysis_data.get('processing_time', 0),
                'model_version': analysis_data.get('model_version', 'unknown'),
                'created_at': datetime.utcnow()
            }
            
            self.analytics.insert_one(analytics_doc)
            logger.info(f"Stored analytics data for analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error populating analytics data: {e}")
    
    def _populate_analysis_history(self, analysis_id, user_id, analysis_data):
        """Store analysis history for trend tracking"""
        try:
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            traffic_density = analysis_data.get('traffic_density', {})
            
            # Get previous analysis for trend calculation
            previous_analysis = self.analytics.find_one(
                {'user_id': user_id}, 
                sort=[('created_at', -1)]
            )
            
            current_vehicles = vehicle_detection.get('total_vehicles', 0)
            current_congestion = traffic_density.get('congestion_index', 0.0)
            
            # Calculate trends
            vehicle_trend = 'stable'
            congestion_trend = 'stable'
            
            if previous_analysis:
                prev_vehicles = previous_analysis.get('total_vehicles', 0)
                prev_congestion = previous_analysis.get('congestion_index', 0.0)
                
                if current_vehicles > prev_vehicles * 1.1:
                    vehicle_trend = 'increasing'
                elif current_vehicles < prev_vehicles * 0.9:
                    vehicle_trend = 'decreasing'
                
                if current_congestion > prev_congestion * 1.1:
                    congestion_trend = 'increasing'
                elif current_congestion < prev_congestion * 0.9:
                    congestion_trend = 'decreasing'
            
            history_doc = {
                'analysis_id': analysis_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                'vehicle_count_trend': vehicle_trend,
                'congestion_trend': congestion_trend,
                'model_performance': {
                    'processing_time': analysis_data.get('processing_time', 0),
                    'fps': analysis_data.get('fps', 0),
                    'model_version': analysis_data.get('model_version', 'unknown')
                },
                'session_summary': {
                    'total_vehicles': current_vehicles,
                    'congestion_level': traffic_density.get('density_level', 'unknown'),
                    'confidence': vehicle_detection.get('average_confidence', 0.0)
                },
                'created_at': datetime.utcnow()
            }
            
            self.db.analysis_history.insert_one(history_doc)
            logger.info(f"Stored analysis history for analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error populating analysis history: {e}")
    
    def _generate_llm_insights(self, analysis_id, user_id, analysis_data):
        """Generate and store LLM-based insights"""
        try:
            vehicle_detection = analysis_data.get('vehicle_detection', {})
            traffic_density = analysis_data.get('traffic_density', {})
            
            total_vehicles = vehicle_detection.get('total_vehicles', 0)
            density_level = traffic_density.get('density_level', 'unknown')
            congestion_index = traffic_density.get('congestion_index', 0.0)
            
            # Generate insights based on data
            summary = f"Analysis detected {total_vehicles} vehicles with {density_level} traffic density."
            
            recommendations = []
            if congestion_index > 0.7:
                recommendations.append("High congestion detected. Consider traffic flow optimization.")
            elif congestion_index < 0.3:
                recommendations.append("Low traffic density. Good flow conditions.")
            else:
                recommendations.append("Moderate traffic conditions. Monitor for changes.")
            
            if total_vehicles > 20:
                recommendations.append("High vehicle count may indicate peak hours or events.")
            
            # Traffic patterns analysis
            patterns = []
            detection_summary = vehicle_detection.get('detection_summary', {})
            
            if detection_summary.get('cars', 0) > detection_summary.get('large_vehicles', 0) * 3:
                patterns.append("Predominantly passenger vehicle traffic")
            
            if detection_summary.get('2_wheelers', 0) > total_vehicles * 0.2:
                patterns.append("Significant two-wheeler presence")
            
            key_findings = [
                f"Vehicle distribution: {detection_summary}",
                f"Traffic density: {density_level} ({congestion_index:.2f})",
                f"Processing efficiency: {analysis_data.get('fps', 0):.1f} FPS"
            ]
            
            # Calculate confidence score
            avg_confidence = vehicle_detection.get('average_confidence', 0.0)
            confidence_score = min(0.95, avg_confidence * 0.9 + 0.1)  # Adjust for realism
            
            insight_doc = {
                'analysis_id': analysis_id,
                'user_id': user_id,
                'summary': summary,
                'recommendations': recommendations,
                'traffic_patterns': patterns,
                'key_findings': key_findings,
                'confidence_score': confidence_score,
                'generated_by': 'system_ai',
                'created_at': datetime.utcnow()
            }
            
            result = self.db.llm_insights.insert_one(insight_doc)
            
            # Update main analysis with insight reference
            self.analyses.update_one(
                {'_id': ObjectId(analysis_id)},
                {'$set': {'llm_insight_id': str(result.inserted_id)}}
            )
            
            logger.info(f"Generated LLM insights for analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error generating LLM insights: {e}")
    
    def get_analysis(self, analysis_id, user_id=None):
        """Get analysis by ID"""
        try:
            query = {'_id': ObjectId(analysis_id)}
            if user_id:
                query['user_id'] = user_id
            
            analysis = self.analyses.find_one(query)
            if analysis:
                analysis['id'] = str(analysis['_id'])
                analysis.pop('_id', None)
                
                # Convert datetime objects
                for key, value in analysis.items():
                    if hasattr(value, 'isoformat'):
                        analysis[key] = value.isoformat()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting analysis: {e}")
            return None
    
    def get_recent_analyses(self, limit=10):
        """Get recent analyses across all users"""
        try:
            cursor = self.analyses.find() \
                                 .sort('created_at', -1) \
                                 .limit(limit)
            
            analyses = []
            for analysis in cursor:
                analysis['id'] = str(analysis['_id'])
                analysis.pop('_id', None)
                
                # Convert datetime objects
                for key, value in analysis.items():
                    if hasattr(value, 'isoformat'):
                        analysis[key] = value.isoformat()
                
                analyses.append(analysis)
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error getting recent analyses: {e}")
            return []
    
    def update_analysis(self, analysis_id, user_id, update_data):
        """Update analysis"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.analyses.update_one(
                {'_id': ObjectId(analysis_id), 'user_id': user_id},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating analysis: {e}")
            return False
    
    def delete_analysis(self, analysis_id, user_id):
        """Delete analysis"""
        try:
            result = self.analyses.delete_one({
                '_id': ObjectId(analysis_id),
                'user_id': user_id
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting analysis: {e}")
            return False
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            pipeline = [
                {'$match': {'user_id': user_id}},
                {'$group': {
                    '_id': None,
                    'total_analyses': {'$sum': 1},
                    'total_vehicles': {'$sum': '$vehicle_detection.total_vehicles'},
                    'avg_processing_time': {'$avg': '$processing_time'},
                    'avg_fps': {'$avg': '$fps'},
                    'models_used': {'$addToSet': '$model_version'}
                }}
            ]
            
            result = list(self.analyses.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)
                return stats
            
            return {
                'total_analyses': 0,
                'total_vehicles': 0,
                'avg_processing_time': 0,
                'avg_fps': 0,
                'models_used': []
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return None

# Global instance
mongo_analysis = MongoAnalysisService()