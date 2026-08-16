"""
Serializers for traffic analysis app - MongoDB compatible
"""
from rest_framework import serializers


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image upload"""
    image = serializers.ImageField(required=True)
    
    def validate_image(self, value):
        """Validate uploaded image"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Maximum size is 10MB.")
        
        # Check file format
        allowed_formats = ['JPEG', 'JPG', 'PNG', 'WEBP']
        if hasattr(value, 'image') and value.image.format not in allowed_formats:
            raise serializers.ValidationError(
                f"Unsupported image format. Allowed formats: {', '.join(allowed_formats)}"
            )
        
        return value


class AnalysisResultSerializer(serializers.Serializer):
    """Serializer for analysis results - MongoDB compatible"""
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    original_image = serializers.CharField(required=False)
    annotated_image = serializers.CharField(required=False)
    file_size = serializers.IntegerField(required=False)
    image_dimensions = serializers.JSONField(required=False)
    processing_time = serializers.FloatField(required=False)
    fps = serializers.FloatField(required=False)
    model_version = serializers.CharField(required=False)
    analysis_type = serializers.CharField(required=False)
    vehicle_detection = serializers.JSONField(required=False)
    scene_classification = serializers.JSONField(required=False)
    traffic_density = serializers.JSONField(required=False)
    traffic_flow = serializers.JSONField(required=False)
    success = serializers.BooleanField(default=True)
    status = serializers.CharField(default='completed')
    
    def to_representation(self, instance):
        """Custom representation with computed fields"""
        data = super().to_representation(instance)
        
        # Add total vehicles count
        if instance.get('vehicle_detection'):
            data['total_vehicles'] = instance['vehicle_detection'].get('total_vehicles', 0)
        
        # Add formatted processing time
        if instance.get('processing_time'):
            data['processing_time_formatted'] = f"{instance['processing_time']:.2f}s"
        
        return data


class VideoAnalysisSerializer(serializers.Serializer):
    """Serializer for video analysis sessions - MongoDB compatible"""
    id = serializers.CharField(read_only=True)
    user_id = serializers.CharField(read_only=True)
    session_id = serializers.CharField(read_only=True)
    video_source = serializers.CharField(required=False)
    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(required=False)
    duration = serializers.FloatField(required=False)
    total_frames_processed = serializers.IntegerField(default=0)
    average_processing_time = serializers.FloatField(required=False)
    max_vehicles_detected = serializers.IntegerField(required=False)
    min_vehicles_detected = serializers.IntegerField(required=False)
    average_vehicles = serializers.FloatField(required=False)
    status = serializers.CharField(default='active')


class ModelPerformanceSerializer(serializers.Serializer):
    """Serializer for model performance metrics - MongoDB compatible"""
    id = serializers.CharField(read_only=True)
    model_name = serializers.CharField()
    version = serializers.CharField()
    date = serializers.DateField()
    accuracy = serializers.FloatField(required=False)
    precision = serializers.FloatField(required=False)
    recall = serializers.FloatField(required=False)
    f1_score = serializers.FloatField(required=False)
    inference_time = serializers.FloatField(required=False)
    memory_usage = serializers.FloatField(required=False)
    dataset_size = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False)
    total_analyses = serializers.IntegerField(default=0)
    average_processing_time = serializers.FloatField(default=0.0)
    average_fps = serializers.FloatField(default=0.0)
    device = serializers.CharField(default='cpu')


class AnalysisStatsSerializer(serializers.Serializer):
    """Serializer for analysis statistics"""
    total_analyses = serializers.IntegerField()
    image_analyses = serializers.IntegerField()
    video_analyses = serializers.IntegerField()
    stream_analyses = serializers.IntegerField()
    average_processing_time = serializers.FloatField()
    total_vehicles_detected = serializers.IntegerField()
    average_vehicles_per_analysis = serializers.FloatField()