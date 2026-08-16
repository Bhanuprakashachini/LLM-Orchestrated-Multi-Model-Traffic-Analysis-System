"""
Serializers for streaming app
"""
from rest_framework import serializers


class StreamConfigSerializer(serializers.Serializer):
    """Serializer for stream configuration"""
    source_type = serializers.ChoiceField(
        choices=['webcam', 'rtsp', 'file'],
        default='webcam'
    )
    source_url = serializers.CharField(required=False, allow_blank=True)
    fps = serializers.IntegerField(default=30, min_value=1, max_value=60)
    resolution = serializers.ChoiceField(
        choices=['640x480', '1280x720', '1920x1080'],
        default='1280x720'
    )
    enable_recording = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validate stream configuration"""
        source_type = attrs.get('source_type')
        source_url = attrs.get('source_url')
        
        if source_type in ['rtsp', 'file'] and not source_url:
            raise serializers.ValidationError(
                f"source_url is required for {source_type} streams"
            )
        
        return attrs


class StreamStatusSerializer(serializers.Serializer):
    """Serializer for stream status"""
    session_id = serializers.CharField()
    status = serializers.ChoiceField(
        choices=['starting', 'running', 'stopped', 'error']
    )
    fps = serializers.FloatField()
    frame_count = serializers.IntegerField()
    duration = serializers.FloatField()
    last_frame_time = serializers.DateTimeField()
    error_message = serializers.CharField(required=False, allow_blank=True)


class StreamFrameSerializer(serializers.Serializer):
    """Serializer for stream frame data"""
    frame_id = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    vehicle_count = serializers.IntegerField()
    vehicles = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    scene_type = serializers.CharField(required=False)
    density_level = serializers.CharField(required=False)
    
    
class StreamSessionSerializer(serializers.Serializer):
    """Serializer for stream session info"""
    session_id = serializers.CharField()
    user_id = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField(required=False)
    total_frames = serializers.IntegerField()
    average_fps = serializers.FloatField()
    total_vehicles = serializers.IntegerField()
    config = StreamConfigSerializer()


class StreamStatsSerializer(serializers.Serializer):
    """Serializer for stream statistics"""
    active_sessions = serializers.IntegerField()
    total_frames_processed = serializers.IntegerField()
    average_processing_time = serializers.FloatField()
    current_fps = serializers.FloatField()
    memory_usage = serializers.FloatField()
    cpu_usage = serializers.FloatField()