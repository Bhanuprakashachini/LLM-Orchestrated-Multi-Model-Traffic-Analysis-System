"""
MongoDB Authentication Service
Uses existing MongoDB collections for user management
"""
import pymongo
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from django.conf import settings
from utils.mongodb import get_mongo_db
import uuid
import logging

logger = logging.getLogger(__name__)

class MongoAuthService:
    """MongoDB-based authentication service"""
    
    def __init__(self):
        self.db = get_mongo_db()
        if self.db is None:
            raise Exception("MongoDB connection failed")
        
        self.users = self.db.users
        self.user_profiles = self.db.user_profiles
        self.user_sessions = self.db.user_sessions
        self.login_attempts = self.db.login_attempts
    
    def create_user(self, username, email, password, first_name='', last_name=''):
        """Create a new user"""
        try:
            # Check if user already exists
            if self.users.find_one({'$or': [{'username': username}, {'email': email}]}):
                return None, "User already exists"
            
            # Create user document
            user_doc = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'password_hash': generate_password_hash(password),
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'created_at': datetime.utcnow(),
                'last_login': None
            }
            
            result = self.users.insert_one(user_doc)
            user_id = str(result.inserted_id)
            
            # Create user profile
            profile_doc = {
                'user_id': user_id,
                'theme': 'light',
                'language': 'en',
                'notifications_enabled': True,
                'email_notifications': True,
                'auto_save_analyses': True,
                'default_analysis_type': 'image',
                'dashboard_layout': {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            self.user_profiles.insert_one(profile_doc)
            
            logger.info(f"User created: {username}")
            return user_id, "User created successfully"
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None, str(e)
    
    def authenticate_user(self, username, password):
        """Authenticate user with username/password"""
        try:
            user = self.users.find_one({'username': username})
            if not user:
                return None, "User not found"
            
            if not user.get('is_active', True):
                return None, "User account is disabled"
            
            if not check_password_hash(user['password_hash'], password):
                return None, "Invalid password"
            
            # Update last login
            self.users.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            
            return user, "Authentication successful"
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None, str(e)
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            from bson import ObjectId
            user = self.users.find_one({'_id': ObjectId(user_id)})
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_profile(self, user_id):
        """Get user profile"""
        try:
            profile = self.user_profiles.find_one({'user_id': user_id})
            if profile:
                # Convert ObjectId to string and remove it
                profile.pop('_id', None)
                return profile
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def create_session(self, user, request):
        """Create user session"""
        try:
            user_id = str(user['_id'])
            session_key = str(uuid.uuid4())
            
            # Get client info
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            device_info = self._parse_device_info(user_agent)
            
            # Create session document
            session_doc = {
                'user_id': user_id,
                'session_key': session_key,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_type': device_info.get('device_type', 'Unknown'),
                'browser': device_info.get('browser', 'Unknown'),
                'operating_system': device_info.get('os', 'Unknown'),
                'location': self._get_location_from_ip(ip_address),
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=24),
                'is_active': True
            }
            
            result = self.user_sessions.insert_one(session_doc)
            
            return {
                'session_id': str(result.inserted_id),
                'session_key': session_key,
                'expires_at': session_doc['expires_at'],
                'device_info': device_info,
                'ip_address': ip_address
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def record_login_attempt(self, username, ip_address, success, request, failure_reason=''):
        """Record login attempt"""
        try:
            attempt_doc = {
                'username': username,
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'success': success,
                'failure_reason': failure_reason,
                'timestamp': datetime.utcnow()
            }
            
            self.login_attempts.insert_one(attempt_doc)
            
        except Exception as e:
            logger.error(f"Error recording login attempt: {e}")
    
    def is_ip_locked(self, ip_address, max_attempts=5, lockout_minutes=30):
        """Check if IP is locked due to failed attempts - DISABLED"""
        # RATE LIMITING DISABLED - Always return False to allow unlimited attempts
        return False
        
        # Original code commented out:
        # try:
        #     since = datetime.utcnow() - timedelta(minutes=lockout_minutes)
        #     
        #     failed_attempts = self.login_attempts.count_documents({
        #         'ip_address': ip_address,
        #         'success': False,
        #         'timestamp': {'$gte': since}
        #     })
        #     
        #     return failed_attempts >= max_attempts
        #     
        # except Exception as e:
        #     logger.error(f"Error checking IP lock: {e}")
        #     return False
    
    def generate_jwt_token(self, user):
        """Generate JWT token using custom JWT generator"""
        try:
            from .mongo_jwt_auth import JWTTokenGenerator
            return JWTTokenGenerator.generate_access_token(str(user['_id']))
            
        except Exception as e:
            logger.error(f"Error generating JWT token: {e}")
            return None
    
    def verify_jwt_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = self.get_user_by_id(payload['user_id'])
            return user
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'
    
    def _parse_device_info(self, user_agent):
        """Parse device info from user agent"""
        device_info = {
            'device_type': 'Desktop',
            'browser': 'Unknown',
            'os': 'Unknown'
        }
        
        user_agent_lower = user_agent.lower()
        
        # Detect device type
        if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone', 'ipad']):
            device_info['device_type'] = 'Mobile'
        elif 'tablet' in user_agent_lower:
            device_info['device_type'] = 'Tablet'
        
        # Detect browser
        if 'chrome' in user_agent_lower:
            device_info['browser'] = 'Chrome'
        elif 'firefox' in user_agent_lower:
            device_info['browser'] = 'Firefox'
        elif 'safari' in user_agent_lower:
            device_info['browser'] = 'Safari'
        elif 'edge' in user_agent_lower:
            device_info['browser'] = 'Edge'
        
        # Detect OS
        if 'windows' in user_agent_lower:
            device_info['os'] = 'Windows'
        elif 'mac' in user_agent_lower:
            device_info['os'] = 'macOS'
        elif 'linux' in user_agent_lower:
            device_info['os'] = 'Linux'
        elif 'android' in user_agent_lower:
            device_info['os'] = 'Android'
        elif 'ios' in user_agent_lower:
            device_info['os'] = 'iOS'
        
        return device_info
    
    def _get_location_from_ip(self, ip_address):
        """Get location from IP (placeholder)"""
        if ip_address.startswith('127.') or ip_address.startswith('192.168.'):
            return 'Local Network'
        return 'Unknown Location'

# Global instance
mongo_auth = MongoAuthService()