"""
Serializers for users app - MongoDB compatible
"""
from rest_framework import serializers


class UserPreferencesSerializer(serializers.Serializer):
    """Serializer for user preferences"""
    theme = serializers.ChoiceField(
        choices=['light', 'dark', 'auto'],
        default='light'
    )
    language = serializers.ChoiceField(
        choices=['en', 'es', 'fr', 'de'],
        default='en'
    )
    notifications_enabled = serializers.BooleanField(default=True)
    email_notifications = serializers.BooleanField(default=True)
    auto_save_analyses = serializers.BooleanField(default=True)
    default_analysis_type = serializers.ChoiceField(
        choices=['image', 'video', 'stream'],
        default='image'
    )
    dashboard_layout = serializers.JSONField(required=False)


class UserActivitySerializer(serializers.Serializer):
    """Serializer for user activity tracking"""
    user_id = serializers.CharField()
    activity_type = serializers.ChoiceField(
        choices=['login', 'logout', 'analysis', 'stream_start', 'stream_end', 'settings_change']
    )
    timestamp = serializers.DateTimeField()
    details = serializers.JSONField(required=False)
    ip_address = serializers.IPAddressField(required=False)
    user_agent = serializers.CharField(required=False)


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_analyses = serializers.IntegerField()
    total_processing_time = serializers.FloatField()
    favorite_analysis_type = serializers.CharField()
    total_vehicles_detected = serializers.IntegerField()
    account_age_days = serializers.IntegerField()
    last_activity = serializers.DateTimeField()
    usage_streak_days = serializers.IntegerField()


class UserQuotaSerializer(serializers.Serializer):
    """Serializer for user quota information"""
    daily_analyses_limit = serializers.IntegerField()
    daily_analyses_used = serializers.IntegerField()
    monthly_analyses_limit = serializers.IntegerField()
    monthly_analyses_used = serializers.IntegerField()
    storage_limit_mb = serializers.FloatField()
    storage_used_mb = serializers.FloatField()
    api_calls_limit = serializers.IntegerField()
    api_calls_used = serializers.IntegerField()


class UserProfileExtendedSerializer(serializers.Serializer):
    """Extended user profile serializer - MongoDB compatible"""
    id = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    preferences = UserPreferencesSerializer(required=False)
    stats = UserStatsSerializer(read_only=True)
    quota = UserQuotaSerializer(read_only=True)


class UserSessionSerializer(serializers.Serializer):
    """Serializer for user session information"""
    session_id = serializers.CharField()
    user_id = serializers.CharField()
    start_time = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()
    ip_address = serializers.IPAddressField()
    user_agent = serializers.CharField()
    is_active = serializers.BooleanField()


class TeamMemberSerializer(serializers.Serializer):
    """Serializer for team member information"""
    user_id = serializers.CharField()
    username = serializers.CharField()
    email = serializers.CharField()
    role = serializers.ChoiceField(
        choices=['admin', 'analyst', 'viewer']
    )
    permissions = serializers.ListField(
        child=serializers.CharField()
    )
    joined_date = serializers.DateTimeField()
    last_active = serializers.DateTimeField()