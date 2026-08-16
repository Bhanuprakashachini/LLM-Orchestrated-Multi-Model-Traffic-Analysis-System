"""
Enhanced Authentication views with MongoDB session management and security
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileSerializer
)
from .services.session_manager import SessionManager
from .mongo_auth import mongo_auth
from .mongo_jwt_auth import JWTTokenGenerator, MongoUser
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(APIView):
    """MongoDB-based login view with session management and security"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User login with MongoDB session management",
        description="Authenticate user and return JWT tokens with user data and session info"
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client IP
        ip_address = mongo_auth._get_client_ip(request)
        
        # RATE LIMITING DISABLED - Allow unlimited login attempts
        # if mongo_auth.is_ip_locked(ip_address):
        #     return Response({
        #         'error': 'Too many failed login attempts. Please try again later.'
        #     }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Authenticate user with MongoDB
        user, message = mongo_auth.authenticate_user(username, password)
        
        if user is not None:
            if user.get('is_active', True):
                # Record successful login
                mongo_auth.record_login_attempt(username, ip_address, True, request)
                
                # Generate JWT tokens using our custom generator
                access_token = JWTTokenGenerator.generate_access_token(str(user['_id']))
                refresh_token = JWTTokenGenerator.generate_refresh_token(str(user['_id']))
                
                # Create session
                session_info = mongo_auth.create_session(user, request)
                
                # Get user profile
                profile = mongo_auth.get_user_profile(str(user['_id']))
                
                return Response({
                    'access': access_token,
                    'refresh': refresh_token,
                    'user': {
                        'id': str(user['_id']),
                        'username': user['username'],
                        'email': user['email'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'profile': profile
                    },
                    'session': session_info
                }, status=status.HTTP_200_OK)
            else:
                mongo_auth.record_login_attempt(username, ip_address, False, request, 'Account disabled')
                return Response({
                    'error': 'Account is disabled'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Record failed login
            mongo_auth.record_login_attempt(username, ip_address, False, request, 'Invalid credentials')
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserRegistrationView(generics.CreateAPIView):
    """MongoDB-based user registration view"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User registration with MongoDB",
        description="Register a new user account with automatic profile creation in MongoDB"
    )
    def post(self, request, *args, **kwargs):
        try:
            # Extract data
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            password_confirm = request.data.get('password_confirm')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            
            # Validate required fields
            if not all([username, email, password, password_confirm]):
                return Response({
                    'error': 'All fields are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate password confirmation
            if password != password_confirm:
                return Response({
                    'error': 'Passwords do not match'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate password length
            if len(password) < 8:
                return Response({
                    'error': 'Password must be at least 8 characters long'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user using MongoDB
            user_id, message = mongo_auth.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            if not user_id:
                return Response({
                    'error': 'Registration failed',
                    'details': message
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the created user
            user = mongo_auth.get_user_by_id(user_id)
            if not user:
                return Response({
                    'error': 'User creation failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Generate JWT tokens using our custom generator
            access_token = JWTTokenGenerator.generate_access_token(str(user['_id']))
            refresh_token = JWTTokenGenerator.generate_refresh_token(str(user['_id']))
            
            # Create session
            session_info = mongo_auth.create_session(user, request)
            
            # Record successful registration
            mongo_auth.record_login_attempt(username, session_info['ip_address'], True, request)
            
            logger.info(f"New user registered: {username}")
            
            return Response({
                'message': 'User registered successfully',
                'access': str(access_token),
                'user': {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name']
                },
                'session': session_info
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return Response({
                'error': 'Registration failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Get current user with session info",
    description="Get current authenticated user information with active sessions"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current user information with session details"""
    try:
        user = request.user  # This is now a MongoUser instance
        
        # Get user profile from MongoDB
        profile = mongo_auth.get_user_profile(user.id)
        
        # Get active sessions (simplified for now)
        active_sessions = []  # TODO: Implement MongoDB session retrieval
        
        return Response({
            'user': user.to_dict(),
            'profile': profile,
            'active_sessions': active_sessions,
            'session_count': len(active_sessions)
        })
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Update user profile with validation",
    description="Update current user profile information with enhanced validation"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile with enhanced validation"""
    try:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update user fields
        user_fields = ['first_name', 'last_name', 'email']
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        # Validate email uniqueness
        if 'email' in request.data:
            if User.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
                return Response({
                    'error': 'Email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        user.save()
        
        # Update profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'message': 'Profile updated successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'profile': serializer.data
            })
        else:
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Enhanced user logout with session management",
    description="Logout user, blacklist refresh token, and terminate session"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Enhanced logout with session management"""
    try:
        user = request.user
        session_manager = SessionManager()
        
        # Get session key from request
        session_key = request.session.session_key
        
        # Terminate current session
        if session_key:
            session_manager.terminate_session(user, session_key)
        
        # Blacklist refresh token if provided
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                logger.warning(f"Error blacklisting token: {e}")
        
        logger.info(f"User logged out: {user.username}")
        
        return Response({
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Get active sessions",
    description="Get all active sessions for the current user"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_sessions(request):
    """Get all active sessions for the user"""
    try:
        user = request.user
        session_manager = SessionManager()
        
        active_sessions = session_manager.get_active_sessions(user)
        
        return Response({
            'active_sessions': active_sessions,
            'session_count': len(active_sessions)
        })
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Terminate all sessions",
    description="Terminate all active sessions for security purposes"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminate_all_sessions(request):
    """Terminate all user sessions (security feature)"""
    try:
        user = request.user
        session_manager = SessionManager()
        
        # Terminate all sessions
        terminated_count = session_manager.terminate_all_sessions(user)
        
        logger.info(f"Terminated {terminated_count} sessions for user {user.username}")
        
        return Response({
            'message': f'Terminated {terminated_count} sessions',
            'terminated_sessions': terminated_count
        })
        
    except Exception as e:
        logger.error(f"Error terminating sessions: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Terminate specific session",
    description="Terminate a specific session by session ID"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def terminate_session(request):
    """Terminate a specific session"""
    try:
        user = request.user
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response({
                'error': 'Session ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session
        try:
            user_session = UserSession.objects.get(id=session_id, user=user, is_active=True)
            session_manager = SessionManager()
            
            success = session_manager.terminate_session(user, user_session.session_key)
            
            if success:
                return Response({
                    'message': 'Session terminated successfully'
                })
            else:
                return Response({
                    'error': 'Failed to terminate session'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except UserSession.DoesNotExist:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Error terminating session: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Get login history",
    description="Get user's recent login history for security monitoring"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_login_history(request):
    """Get user's login history"""
    try:
        user = request.user
        
        # Get recent login attempts
        login_attempts = LoginAttempt.objects.filter(
            username=user.username
        ).order_by('-timestamp')[:20]
        
        history = []
        for attempt in login_attempts:
            history.append({
                'timestamp': attempt.timestamp,
                'ip_address': attempt.ip_address,
                'success': attempt.success,
                'user_agent': attempt.user_agent[:100],  # Truncate for display
                'failure_reason': attempt.failure_reason
            })
        
        return Response({
            'login_history': history,
            'total_attempts': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting login history: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)