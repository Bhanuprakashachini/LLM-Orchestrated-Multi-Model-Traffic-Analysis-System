"""
Serializers for analytics app
"""
from rest_framework import serializers


class TrafficMetricsSerializer(serializers.Serializer):
    """Serializer for traffic metrics"""
    timestamp = serializers.DateTimeField()
    vehicle_count = serializers.IntegerField()
    density_level = serializers.CharField()
    congestion_index = serializers.FloatField()
    
    
class VehicleTypeBreakdownSerializer(serializers.Serializer):
    """Serializer for vehicle type breakdown"""
    cars = serializers.IntegerField()
    motorcycles = serializers.IntegerField()
    buses = serializers.IntegerField()
    trucks = serializers.IntegerField()
    total = serializers.IntegerField()
    timestamp = serializers.DateTimeField()


class TimeSeriesDataSerializer(serializers.Serializer):
    """Serializer for time series analytics data"""
    date_range = serializers.CharField()
    interval = serializers.ChoiceField(
        choices=['hourly', 'daily', 'weekly', 'monthly']
    )
    data_points = serializers.ListField(
        child=TrafficMetricsSerializer()
    )
    summary_stats = serializers.DictField()


class HeatmapDataSerializer(serializers.Serializer):
    """Serializer for heatmap visualization data"""
    grid_size = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    density_matrix = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField())
    )
    max_density = serializers.FloatField()
    min_density = serializers.FloatField()


class TrafficPatternSerializer(serializers.Serializer):
    """Serializer for traffic pattern analysis"""
    pattern_type = serializers.ChoiceField(
        choices=['peak_hours', 'seasonal', 'weekly', 'weather_based']
    )
    description = serializers.CharField()
    confidence = serializers.FloatField()
    data = serializers.DictField()
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class PerformanceMetricsSerializer(serializers.Serializer):
    """Serializer for system performance metrics"""
    processing_fps = serializers.FloatField()
    memory_usage_mb = serializers.FloatField()
    cpu_usage_percent = serializers.FloatField()
    gpu_usage_percent = serializers.FloatField(required=False)
    queue_size = serializers.IntegerField()
    error_rate = serializers.FloatField()
    uptime_hours = serializers.FloatField()


class ComparisonReportSerializer(serializers.Serializer):
    """Serializer for comparison reports"""
    period_1 = serializers.DictField()
    period_2 = serializers.DictField()
    comparison_metrics = serializers.DictField()
    insights = serializers.ListField(
        child=serializers.CharField()
    )
    charts = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


class AlertConfigSerializer(serializers.Serializer):
    """Serializer for alert configuration"""
    alert_type = serializers.ChoiceField(
        choices=['high_congestion', 'low_flow', 'system_error', 'performance_degradation']
    )
    threshold = serializers.FloatField()
    enabled = serializers.BooleanField(default=True)
    notification_methods = serializers.ListField(
        child=serializers.ChoiceField(choices=['email', 'webhook', 'dashboard'])
    )


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    current_vehicle_count = serializers.IntegerField()
    current_congestion_level = serializers.CharField()
    average_processing_time = serializers.FloatField()
    total_analyses_today = serializers.IntegerField()
    system_status = serializers.CharField()
    active_streams = serializers.IntegerField()
    recent_alerts = serializers.ListField(
        child=serializers.DictField()
    )