"""
MongoDB Connection and Utilities
Simple MongoDB integration without MongoEngine
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            mongo_settings = settings.MONGODB_SETTINGS
            
            # Build connection string
            if mongo_settings.get('username') and mongo_settings.get('password'):
                connection_string = f"mongodb://{mongo_settings['username']}:{mongo_settings['password']}@{mongo_settings['host']}:{mongo_settings['port']}/{mongo_settings['database']}?authSource={mongo_settings.get('auth_source', 'admin')}"
            else:
                connection_string = f"mongodb://{mongo_settings['host']}:{mongo_settings['port']}"
            
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client[mongo_settings['database']]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB: %s", mongo_settings['database'])
            
        except Exception as e:
            logger.error("MongoDB connection failed: %s", e)
            self.client = None
            self.db = None
    
    def get_database(self):
        """Get MongoDB database instance"""
        if self.db is None:
            self._connect()
        return self.db
    
    def get_collection(self, collection_name):
        """Get MongoDB collection"""
        db = self.get_database()
        if db is not None:
            return db[collection_name]
        return None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Global MongoDB connection instance
mongo_connection = MongoDBConnection()

def get_mongo_db():
    """Get MongoDB database instance"""
    return mongo_connection.get_database()

def get_mongo_collection(collection_name):
    """Get MongoDB collection"""
    return mongo_connection.get_collection(collection_name)

class TrafficAnalysisService:
    """Service class for traffic analysis MongoDB operations"""
    
    def __init__(self):
        self.collection = get_mongo_collection('traffic_analyses')
    
    def create_analysis(self, analysis_data):
        """Create a new traffic analysis document"""
        if self.collection is None:
            return None
        
        analysis_data['created_at'] = datetime.utcnow()
        analysis_data['updated_at'] = datetime.utcnow()
        
        try:
            result = self.collection.insert_one(analysis_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            return None
    
    def get_analysis(self, analysis_id):
        """Get analysis by ID"""
        if self.collection is None:
            return None
        
        try:
            from bson import ObjectId
            return self.collection.find_one({'_id': ObjectId(analysis_id)})
        except Exception as e:
            logger.error("Error getting analysis: %s", e)
            return None
    
    def get_analyses_by_user(self, user_id, limit=20, skip=0):
        """Get analyses by user ID"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find({'user_id': user_id}) \
                                  .sort('created_at', DESCENDING) \
                                  .limit(limit) \
                                  .skip(skip)
            return list(cursor)
        except Exception as e:
            logger.error("Error getting user analyses: %s", e)
            return []
    
    def get_recent_analyses(self, limit=10):
        """Get recent analyses"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find() \
                                  .sort('created_at', DESCENDING) \
                                  .limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error("Error getting recent analyses: %s", e)
            return []
    
    def update_analysis(self, analysis_id, update_data):
        """Update analysis document"""
        if self.collection is None:
            return False
        
        try:
            from bson import ObjectId
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {'_id': ObjectId(analysis_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error updating analysis: %s", e)
            return False
    
    def delete_analysis(self, analysis_id):
        """Delete analysis document"""
        if self.collection is None:
            return False
        
        try:
            from bson import ObjectId
            result = self.collection.delete_one({'_id': ObjectId(analysis_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error("Error deleting analysis: %s", e)
            return False
    
    def get_analysis_by_id(self, analysis_id):
        """Get analysis by ID (alias for get_analysis)"""
        return self.get_analysis(analysis_id)

class AnalyticsService:
    """Service class for analytics MongoDB operations"""
    
    def __init__(self):
        self.collection = get_mongo_collection('analytics_data')
    
    def record_analysis_metrics(self, metrics_data):
        """Record analysis metrics"""
        if self.collection is None:
            return None
        
        metrics_data['timestamp'] = datetime.utcnow()
        
        try:
            result = self.collection.insert_one(metrics_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error("Error recording metrics: %s", e)
            return None
    
    def get_daily_stats(self, days=30):
        """Get daily statistics"""
        if self.collection is None:
            return []
        
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {'$match': {'timestamp': {'$gte': start_date}}},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$timestamp'},
                        'month': {'$month': '$timestamp'},
                        'day': {'$dayOfMonth': '$timestamp'}
                    },
                    'total_analyses': {'$sum': '$total_analyses'},
                    'total_vehicles': {'$sum': '$total_vehicles'},
                    'avg_congestion': {'$avg': '$avg_congestion'}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            return list(self.collection.aggregate(pipeline))
        except Exception as e:
            logger.error("Error getting daily stats: %s", e)
            return []

# Initialize services
traffic_service = TrafficAnalysisService()
analytics_service = AnalyticsService()