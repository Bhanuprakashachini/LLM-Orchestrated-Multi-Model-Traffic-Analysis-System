"""
Analytics app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reports', views.ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
    path('metrics/', views.AnalyticsViewSet.as_view({'get': 'traffic_metrics'}), name='traffic-metrics'),
    path('heatmap/', views.AnalyticsViewSet.as_view({'post': 'generate_heatmap'}), name='generate-heatmap'),
    path('patterns/', views.AnalyticsViewSet.as_view({'post': 'detect_patterns'}), name='detect-patterns'),
    path('performance/', views.system_performance, name='system-performance'),
    path('dashboard/', views.dashboard_stats, name='dashboard-stats'),
    path('user-stats/', views.user_stats, name='user-stats'),
    path('reports/', views.reports_overview, name='reports-overview'),
]