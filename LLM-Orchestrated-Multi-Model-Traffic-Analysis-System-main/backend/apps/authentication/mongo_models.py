"""
MongoDB Models for Authentication using MongoEngine
"""
from mongoengine import Document, StringField, EmailField, BooleanField, DateTimeField, ListField, DictField, IntField
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from django.conf import settings


class User(Document):
    """MongoDB User model"""
    username = StringField(max_length=150, required=True, unique=True)
    email = EmailField(required=True, unique=True)
    first_name = StringField(max_length=30)
    last_name = StringField(max_length=30)
    password_hash = StringField(required=True)
    
    # Status fields
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    
    # Timestamps
    date_joined = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()
    
    meta = {
        'collection': 'users',
        'indexes': ['username', 'email']
    }
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.save()
    
    def generate_jwt_token(self):
        """Generate JWT token for user"""
        payload = {
            'user_id': str(self.id),
            'username': self.username,
            'email': self.email,
            'exp': datetime.utcnow().timestamp() + 3600  # 1 hour
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    @classmethod
    def verify_jwt_token(cls, token):
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return cls.objects(id=payload['user_id']).first()
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
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
    
    def __str__(self):
        return self.username


class UserProfile(Document):
    """MongoDB User Profile model"""
    user_id = StringField(required=True, unique=True)  # Reference to User._id
    
    # Profile information
    avatar_url = StringField()
    bio = StringField(max_length=500)
    location = StringField(max_length=100)
    website = StringField()
    
    # Preferences
    theme = StringField(max_length=10, choices=['light', 'dark', 'auto'], default='light')
    language = StringField(max_length=10, choices=['en', 'es', 'fr', 'de'], default='en')
    notifications_enabled = BooleanField(default=True)
    email_notifications = BooleanField(default=True)
    
    # Usage preferences
    auto_save_analyses = BooleanField(default=True)
    default_analysis_type = StringField(max_length=10, choices=['image', 'video', 'stream'], default='image')
    dashboard_layout = DictField(default=dict)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'user_profiles',
        'indexes': ['user_id']
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'location': self.location,
            'website': self.website,
            'theme': self.theme,
            'language': self.language,
            'notifications_enabled': self.notifications_enabled,
            'email_notifications': self.email_notifications,
            'auto_save_analyses': self.auto_save_analyses,
            'default_analysis_type': self.default_analysis_type,
            'dashboard_layout': self.dashboard_layout,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserSession(Document):
    """MongoDB User Session model"""
    user_id = StringField(required=True)  # Reference to User._id
    session_key = StringField(required=True, unique=True)
    
    # Session info
    ip_address = StringField(required=True)
    user_agent = StringField()
    device_type = StringField(max_length=50)
    browser = StringField(max_length=50)
    operating_system = StringField(max_length=50)
    location = StringField(max_length=100)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    last_activity = DateTimeField(default=datetime.utcnow)
    expires_at = DateTimeField(required=True)
    logged_out_at = DateTimeField()
    
    # Status
    is_active = BooleanField(default=True)
    
    meta = {
        'collection': 'user_sessions',
        'indexes': ['user_id', 'session_key', 'expires_at']
    }
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'session_key': self.session_key,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_type': self.device_type,
            'browser': self.browser,
            'operating_system': self.operating_system,
            'location': self.location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'logged_out_at': self.logged_out_at.isoformat() if self.logged_out_at else None,
            'is_active': self.is_active
        }


class LoginAttempt(Document):
    """MongoDB Login Attempt model"""
    username = StringField(max_length=150, required=True)
    ip_address = StringField(required=True)
    user_agent = StringField()
    
    # Attempt info
    success = BooleanField(required=True)
    failure_reason = StringField(max_length=100)
    timestamp = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'login_attempts',
        'indexes': ['username', 'ip_address', 'timestamp']
    }
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }