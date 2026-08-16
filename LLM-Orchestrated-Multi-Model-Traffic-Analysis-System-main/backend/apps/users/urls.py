"""
Users app URLs - MongoDB compatible
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Only register ViewSets that actually exist
# router.register(r'teams', views.TeamViewSet, basename='teams')  # Commented out - doesn't exist

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', views.UserManagementViewSet.as_view({'get': 'profile'}), name='user-profile'),
    path('preferences/', views.UserManagementViewSet.as_view({'put': 'preferences', 'patch': 'preferences'}), name='user-preferences'),
    path('activity/', views.UserManagementViewSet.as_view({'get': 'activity'}), name='user-activity'),
    path('statistics/', views.UserManagementViewSet.as_view({'get': 'statistics'}), name='user-statistics'),
    path('notifications/', views.get_notifications, name='user-notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('teams/', views.get_teams, name='user-teams'),
]