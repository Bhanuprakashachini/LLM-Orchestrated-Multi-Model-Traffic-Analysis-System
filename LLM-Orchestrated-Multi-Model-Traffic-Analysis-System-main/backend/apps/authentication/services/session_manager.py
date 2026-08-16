"""
Advanced Session Management Service - MongoDB compatible
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.utils import timezone
from django.core.cache import cache
from pymongo import MongoClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]
users = db.users
user_sessions = db.user_sessions
login_attempts = db.login_attempts


class SessionManager:
    """Advanced session management with security features"""
    
    def __init__(self):
        self.max_sessions_per_user = 5
        self.session_timeout = timedelta(hours=24)
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
    
    def create_session(self, user: Dict[str, Any], request) -> Dict[str, Any]:
        """Create a new user session with security tracking"""
        try:
            # Get client information
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            device_info = self._parse_device_info(user_agent)
            
            # Check for existing sessions and cleanup old ones
            self._cleanup_old_sessions(user)
            
            # Create session record in MongoDB
            session_data = {
                'user_id': str(user.get('_id', user.get('id', ''))),
                'session_key': request.session.session_key,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_type': device_info.get('device_type', 'Unknown'),
                'browser': device_info.get('browser', 'Unknown'),
                'is_active': True,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'expires_at': datetime.utcnow() + self.session_timeout
            }
            
            result = user_sessions.insert_one(session_data)
            session_id = str(result.inserted_id)
            
            # Store session data in cache for quick access
            cache_key = f"user_session_{user.get('_id', user.get('id', ''))}_{request.session.session_key}"
            cache.set(cache_key, {
                'user_id': str(user.get('_id', user.get('id', ''))),
                'session_id': session_id,
                'ip_address': ip_address,
                'created_at': session_data['created_at'].isoformat(),
                'expires_at': session_data['expires_at'].isoformat()
            }, timeout=86400)  # 24 hours
            
            logger.info(f"Session created for user {user.get('username', 'unknown')} from {ip_address}")
            
            return {
                'session_id': session_id,
                'session_key': request.session.session_key,
                'expires_at': session_data['expires_at'],
                'device_info': device_info,
                'ip_address': ip_address
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def validate_session(self, user: Dict[str, Any], session_key: str, request) -> bool:
        """Validate user session with security checks"""
        try:
            user_id = str(user.get('_id', user.get('id', '')))
            
            # Check cache first
            cache_key = f"user_session_{user_id}_{session_key}"
            cached_session = cache.get(cache_key)
            
            if cached_session:
                # Verify IP address hasn't changed (optional security check)
                current_ip = self._get_client_ip(request)
                if cached_session['ip_address'] != current_ip:
                    logger.warning(f"IP address changed for user {user.get('username', 'unknown')}: {cached_session['ip_address']} -> {current_ip}")
                
                return True
            
            # Check MongoDB
            session = user_sessions.find_one({
                'user_id': user_id,
                'session_key': session_key,
                'is_active': True,
                'expires_at': {'$gt': datetime.utcnow()}
            })
            
            if session:
                # Update last activity
                user_sessions.update_one(
                    {'_id': session['_id']},
                    {'$set': {'last_activity': datetime.utcnow()}}
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return False
    
    def terminate_session(self, user: Dict[str, Any], session_key: str) -> bool:
        """Terminate a specific user session"""
        try:
            user_id = str(user.get('_id', user.get('id', '')))
            
            result = user_sessions.update_one(
                {
                    'user_id': user_id,
                    'session_key': session_key,
                    'is_active': True
                },
                {'$set': {'is_active': False}}
            )
            
            if result.modified_count > 0:
                # Remove from cache
                cache_key = f"user_session_{user_id}_{session_key}"
                cache.delete(cache_key)
                
                logger.info(f"Session terminated for user {user.get('username', 'unknown')}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error terminating session: {e}")
            return False
    
    def terminate_all_sessions(self, user: Dict[str, Any]) -> int:
        """Terminate all active sessions for a user"""
        try:
            user_id = str(user.get('_id', user.get('id', '')))
            
            # Get active sessions
            active_sessions = list(user_sessions.find({
                'user_id': user_id,
                'is_active': True
            }))
            
            count = len(active_sessions)
            
            # Update all sessions
            user_sessions.update_many(
                {'user_id': user_id, 'is_active': True},
                {'$set': {'is_active': False}}
            )
            
            # Clear cache
            for session in active_sessions:
                cache_key = f"user_session_{user_id}_{session.get('session_key', '')}"
                cache.delete(cache_key)
            
            logger.info(f"Terminated {count} sessions for user {user.get('username', 'unknown')}")
            return count
            
        except Exception as e:
            logger.error(f"Error terminating all sessions: {e}")
            return 0
    
    def get_active_sessions(self, user: Dict[str, Any]) -> list:
        """Get all active sessions for a user"""
        try:
            user_id = str(user.get('_id', user.get('id', '')))
            
            sessions = list(user_sessions.find({
                'user_id': user_id,
                'is_active': True,
                'expires_at': {'$gt': datetime.utcnow()}
            }).sort('created_at', -1))
            
            return [{
                'id': str(session['_id']),
                'created_at': session.get('created_at'),
                'last_activity': session.get('last_activity'),
                'ip_address': session.get('ip_address'),
                'device_type': session.get('device_type'),
                'browser': session.get('browser'),
                'is_current': session.get('session_key') == getattr(user, 'session_key', None)
            } for session in sessions]
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    def record_login_attempt(self, username: str, ip_address: str, success: bool, request) -> bool:
        """Record login attempt for security monitoring"""
        try:
            attempt_data = {
                'username': username,
                'ip_address': ip_address,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'success': success,
                'failure_reason': '' if success else 'Invalid credentials',
                'timestamp': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            
            login_attempts.insert_one(attempt_data)
            
            # Check for brute force attempts
            if not success:
                recent_attempts = login_attempts.count_documents({
                    'ip_address': ip_address,
                    'success': False,
                    'timestamp': {'$gte': datetime.utcnow() - self.lockout_duration}
                })
                
                if recent_attempts >= self.max_login_attempts:
                    logger.warning(f"Brute force detected from IP {ip_address}")
                    return False  # Account should be locked
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording login attempt: {e}")
            return True
    
    def is_ip_locked(self, ip_address: str) -> bool:
        """Check if IP address is locked due to failed attempts - DISABLED"""
        # RATE LIMITING DISABLED - Always return False to allow unlimited attempts
        return False
        
        # Original code commented out:
        # try:
        #     recent_failures = login_attempts.count_documents({
        #         'ip_address': ip_address,
        #         'success': False,
        #         'timestamp': {'$gte': datetime.utcnow() - self.lockout_duration}
        #     })
        #     
        #     return recent_failures >= self.max_login_attempts
        #     
        # except Exception as e:
        #     logger.error(f"Error checking IP lock status: {e}")
        #     return False
    
    def _cleanup_old_sessions(self, user: Dict[str, Any]):
        """Clean up old and expired sessions"""
        try:
            user_id = str(user.get('_id', user.get('id', '')))
            
            # Remove expired sessions
            user_sessions.delete_many({
                'expires_at': {'$lt': datetime.utcnow()}
            })
            
            # Limit active sessions per user
            active_sessions = list(user_sessions.find({
                'user_id': user_id,
                'is_active': True
            }).sort('created_at', -1))
            
            if len(active_sessions) >= self.max_sessions_per_user:
                old_sessions = active_sessions[self.max_sessions_per_user-1:]
                for session in old_sessions:
                    user_sessions.update_one(
                        {'_id': session['_id']},
                        {'$set': {'is_active': False}}
                    )
                    
                    # Clear cache
                    cache_key = f"user_session_{user_id}_{session.get('session_key', '')}"
                    cache.delete(cache_key)
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'
    
    def _parse_device_info(self, user_agent: str) -> Dict[str, str]:
        """Parse device information from user agent"""
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
    
    def _get_location_from_ip(self, ip_address: str) -> str:
        """Get approximate location from IP address (placeholder)"""
        # In production, you would use a GeoIP service
        if ip_address.startswith('127.') or ip_address.startswith('192.168.'):
            return 'Local Network'
        return 'Unknown Location'