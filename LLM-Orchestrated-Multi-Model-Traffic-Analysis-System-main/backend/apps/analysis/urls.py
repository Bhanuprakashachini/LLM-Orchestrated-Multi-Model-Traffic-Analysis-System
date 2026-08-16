from django.urls import path
from . import views
from . import enhanced_views
from . import views_comprehensive
from . import advanced_views
from . import user_stats_views
from . import video_views

urlpatterns = [
    # Original endpoints
    path('health/', views.health_check, name='health_check'),
    path('recent/', views.get_recent_analyses, name='recent_analyses'),
    path('create/', views.create_analysis, name='create_analysis'),
    path('upload/', views.upload_and_analyze, name='upload_and_analyze'),
    path('history/', views.get_analysis_history, name='analysis_history'),
    path('compare/', views.compare_models, name='compare_models'),
    path('metrics/', views.get_performance_metrics, name='performance_metrics'),
    path('download/<str:analysis_id>/', views.download_report, name='download_report'),
    path('stats/database/', views.database_stats, name='database_stats'),
    path('save/', views.save_analysis_to_database, name='save_analysis'),  # NEW SAVE ENDPOINT
    
    # Video Analysis Endpoints
    path('video/upload/', views.upload_video_analysis, name='upload_video_analysis'),
    path('video/upload-fixed/', views.upload_video_analysis_fixed, name='upload_video_analysis_fixed'),  # NEW FIXED ENDPOINT
    path('video/<str:analysis_id>/', views.get_video_analysis, name='get_video_analysis'),
    path('video/<str:analysis_id>/metrics/', views.get_video_metrics, name='get_video_metrics'),
    path('video/<str:analysis_id>/download/', views.download_video_report, name='download_video_report'),
    
    # Video Serving Endpoints (with CORS support)
    path('video/serve/<path:video_filename>', video_views.serve_annotated_video, name='serve_annotated_video'),
    
    # User-specific statistics and history endpoints
    path('user/dashboard/', user_stats_views.get_user_dashboard_stats, name='user_dashboard_stats'),
    path('user/history/', user_stats_views.get_user_analysis_history, name='user_analysis_history'),
    path('user/trends/', user_stats_views.get_user_analysis_trends, name='user_analysis_trends'),
    path('user/save/', user_stats_views.save_analysis_to_db, name='user_save_analysis'),
    
    # Enhanced endpoints with tracking
    path('enhanced/upload/', enhanced_views.enhanced_upload_and_analyze, name='enhanced_upload_analyze'),
    path('enhanced/batch/', enhanced_views.batch_analyze, name='batch_analyze'),
    path('enhanced/<str:analysis_id>/', enhanced_views.get_enhanced_analysis, name='get_enhanced_analysis'),
    path('enhanced/accuracy/metrics/', enhanced_views.get_accuracy_metrics, name='accuracy_metrics'),
    path('enhanced/accuracy/compare/', enhanced_views.compare_accuracy, name='compare_accuracy'),
    path('enhanced/status/', enhanced_views.system_status, name='enhanced_system_status'),
    
    # Comprehensive model comparison endpoints
    path('comprehensive/compare/', views_comprehensive.comprehensive_model_comparison, name='comprehensive_compare'),
    path('comprehensive/justification/', views_comprehensive.get_model_justification, name='model_justification'),
    path('comprehensive/export-csv/', views_comprehensive.export_comparison_csv, name='export_comparison_csv'),
    path('comprehensive/models/', views_comprehensive.get_available_models, name='available_models'),
    path('comprehensive/guide/', views_comprehensive.get_model_selection_guide, name='model_selection_guide'),
    
    # Advanced Features Endpoints
    path('advanced/analyze/', views.advanced_traffic_analysis, name='advanced_traffic_analysis'),
    path('advanced/ai-scene/', views.ai_scene_analysis, name='ai_scene_analysis'),
    path('advanced/features-status/', views.get_advanced_features_status, name='advanced_features_status'),
    
    # New Advanced Collection Endpoints (must come before the generic analysis_id pattern)
    path('trends/', advanced_views.get_analysis_trends, name='analysis_trends'),
    path('insights/', advanced_views.get_llm_insights, name='llm_insights'),
    path('insights/generate/', advanced_views.generate_llm_insight, name='generate_llm_insight'),
    path('analytics/advanced/', advanced_views.get_advanced_analytics, name='advanced_analytics'),
    
    # Generic analysis by ID (must be last to avoid conflicts)
    path('<str:analysis_id>/', views.get_analysis, name='get_analysis'),
]