from django.urls import path
from . import views

urlpatterns = [
    # LLM Analysis Features
    path('analyze-conditions/', views.analyze_traffic_conditions, name='analyze_traffic_conditions'),
    path('feature-insights/', views.generate_feature_insights, name='generate_feature_insights'),
    path('compare-models/', views.compare_model_performance, name='compare_model_performance'),
    path('generate-summary/', views.generate_traffic_summary, name='generate_traffic_summary'),
    path('generate-recommendations/', views.generate_recommendations, name='generate_recommendations'),
    path('natural-language-query/', views.handle_natural_language_query, name='natural_language_query'),
    
    # History and Data Retrieval
    path('insights/', views.get_traffic_insights, name='get_traffic_insights'),
    path('descriptions/', views.get_scene_descriptions, name='get_scene_descriptions'),
    path('conversations/', views.get_conversation_history, name='get_conversation_history'),
    path('conversations/<int:session_id>/', views.delete_conversation, name='delete_conversation'),
]