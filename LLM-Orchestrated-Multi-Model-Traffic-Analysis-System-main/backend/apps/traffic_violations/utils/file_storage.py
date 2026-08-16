"""
File-based storage utilities for traffic violations
No database integration - all data stored in JSON files
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid


class FileStorage:
    """File-based storage for traffic violations data"""
    
    def __init__(self):
        self.data_dir = 'traffic_violations_data'
        self.violations_file = os.path.join(self.data_dir, 'violations.json')
        self.statistics_file = os.path.join(self.data_dir, 'statistics.json')
        self.sessions_file = os.path.join(self.data_dir, 'sessions.json')
        self.videos_dir = os.path.join(self.data_dir, 'uploaded_videos')
        
        self.ensure_directories()
        self.ensure_files()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
    
    def ensure_files(self):
        """Create JSON files with initial structure if they don't exist"""
        if not os.path.exists(self.violations_file):
            self._write_json(self.violations_file, {'violations': []})
        
        if not os.path.exists(self.statistics_file):
            initial_stats = {
                'total_violations': 0,
                'speed_violations': 0,
                'helmet_violations': 0,
                'red_light_violations': 0,
                'vehicle_counts': {
                    'cars': 0,
                    'bikes': 0,
                    'buses': 0,
                    'trucks': 0,
                    'total': 0
                },
                'last_updated': datetime.now().isoformat()
            }
            self._write_json(self.statistics_file, initial_stats)
        
        if not os.path.exists(self.sessions_file):
            self._write_json(self.sessions_file, {'sessions': []})
    
    def _read_json(self, file_path: str) -> Dict:
        """Read JSON file safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, file_path: str, data: Dict):
        """Write JSON file safely"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
    
    def save_violation(self, violation_data: Dict) -> str:
        """Save a traffic violation"""
        violation_id = str(uuid.uuid4())
        violation = {
            'id': violation_id,
            'timestamp': datetime.now().isoformat(),
            **violation_data
        }
        
        # Read current violations
        data = self._read_json(self.violations_file)
        if 'violations' not in data:
            data['violations'] = []
        
        # Add new violation
        data['violations'].append(violation)
        
        # Keep only last 1000 violations to prevent file from growing too large
        if len(data['violations']) > 1000:
            data['violations'] = data['violations'][-1000:]
        
        # Save violations
        self._write_json(self.violations_file, data)
        
        # Update statistics
        self._update_statistics(violation_data)
        
        return violation_id
    
    def get_violations(self, limit: int = 50) -> List[Dict]:
        """Get recent violations"""
        data = self._read_json(self.violations_file)
        violations = data.get('violations', [])
        
        # Return most recent violations
        return violations[-limit:] if violations else []
    
    def get_violations_by_session(self, session_id: str) -> List[Dict]:
        """Get violations for a specific session"""
        data = self._read_json(self.violations_file)
        violations = data.get('violations', [])
        
        return [v for v in violations if v.get('session_id') == session_id]
    
    def _update_statistics(self, violation_data: Dict):
        """Update statistics after adding a violation"""
        stats = self._read_json(self.statistics_file)
        
        # Update violation counts
        stats['total_violations'] = stats.get('total_violations', 0) + 1
        
        violation_type = violation_data.get('type', '').upper()
        if violation_type == 'OVERSPEEDING':
            stats['speed_violations'] = stats.get('speed_violations', 0) + 1
        elif violation_type == 'NO_HELMET':
            stats['helmet_violations'] = stats.get('helmet_violations', 0) + 1
        elif violation_type == 'RED_LIGHT_VIOLATION':
            stats['red_light_violations'] = stats.get('red_light_violations', 0) + 1
        
        # Update vehicle counts
        vehicle_type = violation_data.get('vehicle_type', '').lower()
        if 'vehicle_counts' not in stats:
            stats['vehicle_counts'] = {'cars': 0, 'bikes': 0, 'buses': 0, 'trucks': 0, 'total': 0}
        
        if vehicle_type in ['car', 'cars']:
            stats['vehicle_counts']['cars'] += 1
        elif vehicle_type in ['bike', 'motorcycle', 'bikes']:
            stats['vehicle_counts']['bikes'] += 1
        elif vehicle_type in ['bus', 'buses']:
            stats['vehicle_counts']['buses'] += 1
        elif vehicle_type in ['truck', 'trucks']:
            stats['vehicle_counts']['trucks'] += 1
        
        stats['vehicle_counts']['total'] += 1
        stats['last_updated'] = datetime.now().isoformat()
        
        self._write_json(self.statistics_file, stats)
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        return self._read_json(self.statistics_file)
    
    def reset_statistics(self):
        """Reset all statistics"""
        initial_stats = {
            'total_violations': 0,
            'speed_violations': 0,
            'helmet_violations': 0,
            'red_light_violations': 0,
            'vehicle_counts': {
                'cars': 0,
                'bikes': 0,
                'buses': 0,
                'trucks': 0,
                'total': 0
            },
            'last_updated': datetime.now().isoformat()
        }
        self._write_json(self.statistics_file, initial_stats)
    
    def save_session(self, session_data: Dict) -> str:
        """Save a detection session"""
        session_id = str(uuid.uuid4())
        session = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            **session_data
        }
        
        # Read current sessions
        data = self._read_json(self.sessions_file)
        if 'sessions' not in data:
            data['sessions'] = []
        
        # Add new session
        data['sessions'].append(session)
        
        # Keep only last 100 sessions
        if len(data['sessions']) > 100:
            data['sessions'] = data['sessions'][-100:]
        
        # Save sessions
        self._write_json(self.sessions_file, data)
        
        return session_id
    
    def get_sessions(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get recent sessions"""
        data = self._read_json(self.sessions_file)
        sessions = data.get('sessions', [])
        
        if user_id:
            sessions = [s for s in sessions if s.get('user_id') == user_id]
        
        return sessions[-limit:] if sessions else []
    
    def update_session(self, session_id: str, update_data: Dict):
        """Update an existing session"""
        data = self._read_json(self.sessions_file)
        sessions = data.get('sessions', [])
        
        for session in sessions:
            if session.get('session_id') == session_id:
                session.update(update_data)
                session['updated_at'] = datetime.now().isoformat()
                break
        
        self._write_json(self.sessions_file, data)
    
    def save_uploaded_video(self, video_file, filename: str) -> str:
        """Save uploaded video file"""
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(self.videos_dir, safe_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        return file_path
    
    def list_uploaded_videos(self) -> List[Dict]:
        """List all uploaded videos"""
        videos = []
        
        if os.path.exists(self.videos_dir):
            for filename in os.listdir(self.videos_dir):
                file_path = os.path.join(self.videos_dir, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    videos.append({
                        'name': filename,
                        'path': file_path,
                        'size': f"{file_size / (1024 * 1024):.1f} MB",
                        'created_at': datetime.fromtimestamp(
                            os.path.getctime(file_path)
                        ).isoformat()
                    })
        
        # Sort by creation time (newest first)
        videos.sort(key=lambda x: x['created_at'], reverse=True)
        return videos
    
    def cleanup_old_files(self, days: int = 30):
        """Clean up old files (videos and data older than specified days)"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Clean up old videos
        if os.path.exists(self.videos_dir):
            for filename in os.listdir(self.videos_dir):
                file_path = os.path.join(self.videos_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getctime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            print(f"Cleaned up old video: {filename}")
                        except Exception as e:
                            print(f"Error cleaning up {filename}: {e}")


# Global instance
file_storage = FileStorage()