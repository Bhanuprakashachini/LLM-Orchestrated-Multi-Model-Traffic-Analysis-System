"""
URL configuration for Traffic Violations app
"""

from django.urls import path
from django.http import JsonResponse

def test_endpoint(request):
    """Simple test endpoint"""
    return JsonResponse({
        'status': 'success',
        'message': 'Traffic violations app is working!',
        'app': 'traffic_violations'
    })

# Use detection views with full functionality
from . import detection_views as views

app_name = 'traffic_violations'

urlpatterns = [
    # Test endpoint
    path('test/', test_endpoint, name='test'),
    
    # Video management
    path('upload/', views.upload_video, name='upload_video'),
    path('videos/', views.list_videos, name='list_videos'),
    
    # Detection control
    path('start/', views.start_detection, name='start_detection'),
    path('stop/', views.stop_detection, name='stop_detection'),
    path('settings/', views.handle_settings, name='handle_settings'),
    
    # Real-time data
    path('frame/', views.get_frame, name='get_frame'),
    path('violations/', views.get_violations, name='get_violations'),
    path('statistics/', views.get_statistics, name='get_statistics'),
    
    # Session management
    path('session/reset/', views.reset_session, name='reset_session'),
    path('session/export/', views.export_session, name='export_session'),
    
    # Model management
    path('models/', views.get_available_models, name='get_available_models'),
    path('models/switch/', views.switch_model, name='switch_model'),
]