"""
Serializers for LLM integration app
"""
from rest_framework import serializers


class LLMQuerySerializer(serializers.Serializer):
    """Serializer for LLM queries"""
    query = serializers.CharField(max_length=1000)
    context_type = serializers.ChoiceField(
        choices=['analysis', 'traffic_flow', 'scene_description', 'recommendations'],
        default='analysis'
    )
    analysis_id = serializers.IntegerField(required=False)
    include_technical_details = serializers.BooleanField(default=False)
    
    def validate_query(self, value):
        """Validate query content"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Query must be at least 10 characters long")
        return value.strip()


class LLMResponseSerializer(serializers.Serializer):
    """Serializer for LLM responses"""
    query = serializers.CharField()
    response = serializers.CharField()
    context_type = serializers.CharField()
    analysis_id = serializers.IntegerField(required=False)
    processing_time = serializers.FloatField()
    token_count = serializers.IntegerField()
    model_used = serializers.CharField()
    timestamp = serializers.DateTimeField()


class TrafficInsightSerializer(serializers.Serializer):
    """Serializer for traffic insights"""
    insight_type = serializers.ChoiceField(
        choices=['congestion_analysis', 'flow_prediction', 'pattern_detection', 'recommendations']
    )
    title = serializers.CharField()
    description = serializers.CharField()
    confidence_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    data_points = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class SceneDescriptionSerializer(serializers.Serializer):
    """Serializer for AI-generated scene descriptions"""
    analysis_id = serializers.IntegerField()
    description = serializers.CharField()
    key_observations = serializers.ListField(
        child=serializers.CharField()
    )
    traffic_conditions = serializers.CharField()
    weather_assessment = serializers.CharField(required=False)
    time_of_day = serializers.CharField(required=False)
    congestion_level = serializers.CharField()
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class LLMConfigSerializer(serializers.Serializer):
    """Serializer for LLM configuration"""
    provider = serializers.ChoiceField(
        choices=['openai', 'anthropic', 'local'],
        default='openai'
    )
    model = serializers.CharField(default='gpt-3.5-turbo')
    temperature = serializers.FloatField(min_value=0.0, max_value=2.0, default=0.7)
    max_tokens = serializers.IntegerField(min_value=100, max_value=4000, default=1000)
    system_prompt = serializers.CharField(required=False)


class ConversationHistorySerializer(serializers.Serializer):
    """Serializer for conversation history"""
    session_id = serializers.CharField()
    messages = serializers.ListField(
        child=serializers.DictField()
    )
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    message_count = serializers.IntegerField()


class LLMUsageStatsSerializer(serializers.Serializer):
    """Serializer for LLM usage statistics"""
    total_queries = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    most_common_query_type = serializers.CharField()
    daily_usage = serializers.ListField(
        child=serializers.DictField()
    )
    cost_estimate = serializers.FloatField(required=False)