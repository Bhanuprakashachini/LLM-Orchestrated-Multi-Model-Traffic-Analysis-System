"""
MongoDB Models for Traffic Analysis using MongoEngine
"""

from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime
from enum import Enum

class CongestionLevel(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class AnalysisStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

class DetectedObject(EmbeddedDocument):
    """Embedded document for detected objects in traffic analysis"""
    object_class = fields.StringField(required=True, max_length=50)
    confidence = fields.FloatField(required=True, min_value=0.0, max_value=1.0)
    bbox = fields.ListField(fields.FloatField(), max_length=4)  # [x1, y1, x2, y2]
    center_point = fields.ListField(fields.FloatField(), max_length=2)  # [x, y]
    area = fields.FloatField()
    
    meta = {
        'indexes': [
            'object_class',
            'confidence'
        ]
    }

class AnalysisMetadata(EmbeddedDocument):
    """Metadata for analysis process"""
    model_used = fields.StringField(required=True, choices=['yolov8', 'yolov12', 'auto'])
    processing_time = fields.FloatField(required=True)
    image_dimensions = fields.ListField(fields.IntField(), max_length=2)  # [width, height]
    file_size = fields.IntField()  # in bytes
    image_format = fields.StringField(max_length=10)
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    gpu_used = fields.BooleanField(default=False)
    memory_usage = fields.FloatField()  # in MB

class LLMInsights(EmbeddedDocument):
    """LLM-generated insights and recommendations"""
    summary = fields.StringField(max_length=1000)
    recommendations = fields.ListField(fields.StringField(max_length=500))
    traffic_patterns = fields.StringField(max_length=1000)
    congestion_analysis = fields.StringField(max_length=1000)
    suggested_improvements = fields.ListField(fields.StringField(max_length=500))
    confidence_score = fields.FloatField(min_value=0.0, max_value=1.0)
    llm_model = fields.StringField(max_length=50)
    processing_time = fields.FloatField()

class VehicleTrack(EmbeddedDocument):
    """Vehicle tracking information across frames"""
    track_id = fields.IntField(required=True)
    vehicle_class = fields.StringField(required=True, max_length=50)
    first_frame = fields.IntField(required=True)
    last_frame = fields.IntField(required=True)
    positions = fields.ListField(fields.ListField(fields.FloatField(), max_length=2))  # [(x,y), ...]
    speeds = fields.ListField(fields.FloatField())  # Speed at each frame
    avg_speed = fields.FloatField()
    max_speed = fields.FloatField()
    confidence_scores = fields.ListField(fields.FloatField())
    avg_confidence = fields.FloatField()
    
class FrameAnalysis(EmbeddedDocument):
    """Analysis results for individual video frame"""
    frame_number = fields.IntField(required=True)
    timestamp = fields.FloatField(required=True)  # Time in seconds
    vehicle_count = fields.IntField(required=True, min_value=0)
    vehicle_counts = fields.DictField()  # {vehicle_type: count}
    detected_objects = fields.ListField(fields.EmbeddedDocumentField(DetectedObject))
    density_level = fields.StringField(choices=[level.value for level in CongestionLevel])
    congestion_index = fields.FloatField(min_value=0.0, max_value=1.0)
    processing_time = fields.FloatField()
    
class VideoMetadata(EmbeddedDocument):
    """Video file metadata"""
    duration = fields.FloatField(required=True)  # Duration in seconds
    fps = fields.FloatField(required=True)
    total_frames = fields.IntField(required=True)
    resolution = fields.ListField(fields.IntField(), max_length=2)  # [width, height]
    file_size = fields.IntField()  # in bytes
    format = fields.StringField(max_length=20)
    codec = fields.StringField(max_length=50)
    bitrate = fields.IntField()
    
class TrafficMetrics(EmbeddedDocument):
    """Comprehensive traffic metrics"""
    # Vehicle Density Metrics
    avg_vehicle_count = fields.FloatField()
    max_vehicle_count = fields.IntField()
    min_vehicle_count = fields.IntField()
    peak_congestion_time = fields.FloatField()  # Time in seconds
    
    # Traffic Flow Metrics
    vehicles_per_minute = fields.FloatField()
    
    # Congestion Analysis
    congestion_duration = fields.FloatField()  # Seconds of high congestion
    congestion_percentage = fields.FloatField()  # % of video with high congestion
    traffic_buildup_rate = fields.FloatField()  # vehicles/minute increase
    
    # Model Performance
    avg_processing_fps = fields.FloatField()
    total_processing_time = fields.FloatField()
    detection_accuracy = fields.FloatField()
    
class ModelComparison(EmbeddedDocument):
    """Model comparison results"""
    yolov8_results = fields.DictField()
    yolov12_results = fields.DictField()
    best_model = fields.StringField(max_length=20)
    accuracy_difference = fields.FloatField()
    speed_difference = fields.FloatField()
    confidence_difference = fields.FloatField()
    recommendation = fields.StringField(max_length=500)

class TrafficAnalysis(Document):
    """Main document for traffic analysis results"""
    
    # Basic Information
    user_id = fields.StringField(max_length=100)
    session_id = fields.StringField(max_length=100)
    
    # File Information
    file_path = fields.StringField(required=True, max_length=500)
    file_type = fields.StringField(required=True, choices=['image', 'video'], max_length=10)
    analyzed_file_path = fields.StringField(max_length=500)
    thumbnail_path = fields.StringField(max_length=500)
    
    # Video-specific fields
    video_metadata = fields.EmbeddedDocumentField(VideoMetadata)
    frame_analyses = fields.ListField(fields.EmbeddedDocumentField(FrameAnalysis))
    vehicle_tracks = fields.ListField(fields.EmbeddedDocumentField(VehicleTrack))
    
    # Analysis Results
    vehicle_count = fields.IntField(required=True, min_value=0)
    vehicle_counts = fields.DictField()  # {vehicle_type: count}
    congestion_level = fields.StringField(
        required=True, 
        choices=[level.value for level in CongestionLevel]
    )
    congestion_index = fields.FloatField(required=True, min_value=0.0, max_value=1.0)
    
    # Enhanced Metrics
    traffic_metrics = fields.EmbeddedDocumentField(TrafficMetrics)
    model_comparison = fields.EmbeddedDocumentField(ModelComparison)
    
    # Detected Objects (for images or aggregated for videos)
    detected_objects = fields.ListField(fields.EmbeddedDocumentField(DetectedObject))
    
    # Analysis Metadata
    analysis_metadata = fields.EmbeddedDocumentField(AnalysisMetadata, required=True)
    
    # LLM Insights (optional)
    llm_insights = fields.EmbeddedDocumentField(LLMInsights)
    
    # Status and Timestamps
    status = fields.StringField(
        required=True,
        choices=[status.value for status in AnalysisStatus],
        default=AnalysisStatus.PENDING.value
    )
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    completed_at = fields.DateTimeField()
    
    # Additional Fields
    tags = fields.ListField(fields.StringField(max_length=50))
    notes = fields.StringField(max_length=1000)
    is_public = fields.BooleanField(default=False)
    
    meta = {
        'collection': 'traffic_analyses',
        'indexes': [
            'created_at',
            'user_id',
            'congestion_level',
            'vehicle_count',
            'status',
            ('user_id', 'created_at'),
            ('congestion_level', 'created_at'),
        ],
        'ordering': ['-created_at']
    }
    
    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        if self.status == AnalysisStatus.COMPLETED.value and not self.completed_at:
            self.completed_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'image_path': self.image_path,
            'analyzed_image_path': self.analyzed_image_path,
            'vehicle_count': self.vehicle_count,
            'congestion_level': self.congestion_level,
            'congestion_index': self.congestion_index,
            'detected_objects': [
                {
                    'object_class': obj.object_class,
                    'confidence': obj.confidence,
                    'bbox': obj.bbox
                } for obj in self.detected_objects
            ],
            'analysis_metadata': {
                'model_used': self.analysis_metadata.model_used,
                'processing_time': self.analysis_metadata.processing_time,
                'timestamp': self.analysis_metadata.timestamp.isoformat()
            } if self.analysis_metadata else None,
            'llm_insights': {
                'summary': self.llm_insights.summary,
                'recommendations': self.llm_insights.recommendations,
                'traffic_patterns': self.llm_insights.traffic_patterns
            } if self.llm_insights else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AnalyticsData(Document):
    """Document for storing analytics and metrics"""
    
    date = fields.DateTimeField(required=True)
    hour = fields.IntField(min_value=0, max_value=23)
    
    # Traffic Metrics
    total_analyses = fields.IntField(default=0)
    total_vehicles = fields.IntField(default=0)
    avg_congestion = fields.FloatField(default=0.0)
    
    # Congestion Distribution
    low_congestion_count = fields.IntField(default=0)
    medium_congestion_count = fields.IntField(default=0)
    high_congestion_count = fields.IntField(default=0)
    
    # Model Usage
    yolov8_usage = fields.IntField(default=0)
    yolov12_usage = fields.IntField(default=0)
    auto_selection_usage = fields.IntField(default=0)
    
    # Performance Metrics
    avg_processing_time = fields.FloatField(default=0.0)
    total_processing_time = fields.FloatField(default=0.0)
    
    created_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'analytics_data',
        'indexes': [
            'date',
            'hour',
            ('date', 'hour'),
        ],
        'ordering': ['-date', '-hour']
    }

class UserSession(Document):
    """Document for tracking user sessions"""
    
    user_id = fields.StringField(required=True, max_length=100)
    session_id = fields.StringField(required=True, max_length=100)
    
    # Session Information
    ip_address = fields.StringField(max_length=45)
    user_agent = fields.StringField(max_length=500)
    
    # Activity Tracking
    analyses_count = fields.IntField(default=0)
    last_activity = fields.DateTimeField(default=datetime.utcnow)
    
    # Session Timestamps
    session_start = fields.DateTimeField(default=datetime.utcnow)
    session_end = fields.DateTimeField()
    is_active = fields.BooleanField(default=True)
    
    meta = {
        'collection': 'user_sessions',
        'indexes': [
            'user_id',
            'session_id',
            'session_start',
            'is_active',
            ('user_id', 'session_start'),
        ],
        'ordering': ['-session_start']
    }

class SystemLog(Document):
    """Document for system logs and events"""
    
    level = fields.StringField(
        required=True,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    )
    message = fields.StringField(required=True, max_length=1000)
    module = fields.StringField(max_length=100)
    function = fields.StringField(max_length=100)
    
    # Context Information
    user_id = fields.StringField(max_length=100)
    session_id = fields.StringField(max_length=100)
    analysis_id = fields.StringField(max_length=100)
    
    # Additional Data
    extra_data = fields.DictField()
    
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'system_logs',
        'indexes': [
            'level',
            'timestamp',
            'module',
            'user_id',
            ('level', 'timestamp'),
        ],
        'ordering': ['-timestamp']
    }