from django.urls import path
from . import views

urlpatterns = [
    # JWT Authentication
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Disabled - using custom JWT
    
    # User management
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('user/', views.current_user, name='current_user'),
    path('profile/', views.update_profile, name='update_profile'),
    path('logout/', views.logout_view, name='logout'),
    
    # Session management
    path('sessions/', views.get_active_sessions, name='active_sessions'),
    path('sessions/terminate-all/', views.terminate_all_sessions, name='terminate_all_sessions'),
    path('sessions/terminate/', views.terminate_session, name='terminate_session'),
    path('login-history/', views.get_login_history, name='login_history'),
]