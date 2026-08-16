"""
Custom JWT Authentication for MongoDB Users - No Django Auth Dependencies
"""
import jwt
import datetime
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .mongo_auth import mongo_auth
import logging

logger = logging.getLogger(__name__)

# JWT Secret Key - use Django secret key or custom one
JWT_SECRET_KEY = getattr(settings, 'SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = datetime.timedelta(hours=1)
JWT_REFRESH_TOKEN_LIFETIME = datetime.timedelta(days=7)

class MongoUser:
    """
    A user class that mimics Django's User model but works with MongoDB
    """
    def __init__(self, mongo_user_data):
        self.mongo_data = mongo_user_data
        self.id = str(mongo_user_data['_id'])
        self.username = mongo_user_data.get('username', '')
        self.email = mongo_user_data.get('email', '')
        self.first_name = mongo_user_data.get('first_name', '')
        self.last_name = mongo_user_data.get('last_name', '')
        self.is_active = mongo_user_data.get('is_active', True)
        self.is_staff = mongo_user_data.get('is_staff', False)
        self.is_superuser = mongo_user_data.get('is_superuser', False)
        self.date_joined = mongo_user_data.get('date_joined')
        self.last_login = mongo_user_data.get('last_login')
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_username(self):
        return self.username
    
    def __str__(self):
        return self.username
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class JWTTokenGenerator:
    """
    JWT Token generator and validator
    """
    
    @staticmethod
    def generate_access_token(user_id):
        """Generate access token"""
        payload = {
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + JWT_ACCESS_TOKEN_LIFETIME,
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def generate_refresh_token(user_id):
        """Generate refresh token"""
        payload = {
            'user_id': str(user_id),
            'exp': datetime.datetime.utcnow() + JWT_REFRESH_TOKEN_LIFETIME,
            'iat': datetime.datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def validate_token(token):
        """Validate and decode token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

class MongoJWTAuthentication(BaseAuthentication):
    """
    Custom JWT Authentication that works with MongoDB users
    """
    
    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication. Otherwise returns `None`.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        try:
            # Extract token from header
            token = auth_header.split(' ')[1]
            
            # Validate token
            payload = JWTTokenGenerator.validate_token(token)
            
            # Get user from MongoDB
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Token contained no user identification')
            
            mongo_user_data = mongo_auth.get_user_by_id(user_id)
            if not mongo_user_data:
                raise AuthenticationFailed('User not found')
            
            if not mongo_user_data.get('is_active', True):
                raise AuthenticationFailed('User is inactive')
            
            # Return MongoUser instance and token
            user = MongoUser(mongo_user_data)
            return (user, token)
            
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"JWT Authentication error: {e}")
            raise AuthenticationFailed('Invalid authentication')
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return 'Bearer'