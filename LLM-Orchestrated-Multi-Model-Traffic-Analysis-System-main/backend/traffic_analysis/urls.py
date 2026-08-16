"""
URL configuration for traffic_analysis project - MongoDB compatible
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def api_root(request):
    """Root API endpoint"""
    return JsonResponse({
        'message': 'TrafficAI System API',
        'version': '1.0.0',
        'description': 'LLM Orchestrated Multi Model Traffic Analysis System - MongoDB Edition',
        'status': 'online',
        'database': 'MongoDB',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'analysis': '/api/v1/analysis/',
            'streaming': '/api/v1/streaming/',
            'llm': '/api/v1/llm/',
            'analytics': '/api/v1/analytics/',
            'users': '/api/v1/users/',
            'traffic-violations': '/api/v1/traffic-violations/',
            'docs': '/api/docs/'
        }
    })

urlpatterns = [
    # Root endpoint
    path('', api_root, name='api-root'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/analysis/', include('apps.analysis.urls')),
    path('api/v1/streaming/', include('apps.streaming.urls')),
    path('api/v1/llm/', include('apps.llm_integration.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/traffic-violations/', include('apps.traffic_violations.urls')),
]

# Serve media files (always enabled for video streaming)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)