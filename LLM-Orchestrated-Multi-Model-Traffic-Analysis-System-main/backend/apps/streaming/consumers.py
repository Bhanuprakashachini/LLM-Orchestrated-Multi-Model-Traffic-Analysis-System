"""
WebSocket consumers for real-time video streaming and analysis - MongoDB compatible
"""
import json
import asyncio
import base64
import cv2
import numpy as np
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings

from apps.analysis.services.yolov12_analyzer import YOLOv12TrafficAnalyzer

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]
users = db.users
video_analyses = db.video_analyses
frame_analyses = db.frame_analyses


class VideoStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time video stream analysis
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analyzer = None
        self.video_analysis = None
        self.frame_count = 0
        self.processing_queue = asyncio.Queue(maxsize=10)  # Limit queue size
        self.is_processing = False
        
    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        
        # Initialize analyzer
        try:
            self.analyzer = YOLOv12TrafficAnalyzer(model_size='nano', device='cpu')  # Use nano for speed
            logger.info("YOLOv12 analyzer initialized for streaming")
        except Exception as e:
            logger.error(f"Failed to initialize analyzer: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to initialize AI analyzer'
            }))
            return
        
        # Start frame processing task
        asyncio.create_task(self.process_frames())
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to video analysis service'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.video_analysis:
            await self.end_video_session()
        
        logger.info(f"WebSocket disconnected with code: {close_code}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_session':
                await self.start_video_session(data)
            elif message_type == 'video_frame':
                await self.handle_video_frame(data)
            elif message_type == 'stop_stream':
                await self.end_video_session()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def start_video_session(self, data):
        """Start a new video analysis session"""
        try:
            user = await self.get_user()
            if not user:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                return
            
            # Create video analysis session in MongoDB
            import uuid
            session_id = str(uuid.uuid4())
            
            session_data = {
                'user_id': str(user.get('_id', user.get('id', ''))),
                'session_id': session_id,
                'video_source': data.get('source', 'webcam'),
                'start_time': datetime.utcnow(),
                'status': 'active',
                'total_frames_processed': 0,
                'created_at': datetime.utcnow()
            }
            
            result = await database_sync_to_async(video_analyses.insert_one)(session_data)
            self.video_analysis = {**session_data, '_id': result.inserted_id}
            
            self.frame_count = 0
            
            await self.send(text_data=json.dumps({
                'type': 'session_started',
                'session_id': session_id,
                'message': 'Video analysis session started'
            }))
            
            logger.info(f"Started video session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to start video session: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to start session'
            }))
    
    async def handle_video_frame(self, data):
        """Handle incoming video frame"""
        if not self.video_analysis:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'No active session'
            }))
            return
        
        try:
            # Decode base64 frame
            frame_data = data.get('frame')
            if not frame_data:
                return
            
            # Add frame to processing queue (non-blocking)
            try:
                self.processing_queue.put_nowait({
                    'frame_data': frame_data,
                    'timestamp': data.get('timestamp', timezone.now().timestamp()),
                    'frame_number': self.frame_count
                })
                self.frame_count += 1
            except asyncio.QueueFull:
                # Skip frame if queue is full (maintain real-time performance)
                logger.debug("Frame queue full, skipping frame")
                pass
                
        except Exception as e:
            logger.error(f"Error handling video frame: {e}")
    
    async def process_frames(self):
        """Process frames from the queue"""
        while True:
            try:
                # Get frame from queue
                frame_info = await self.processing_queue.get()
                
                if self.is_processing:
                    continue  # Skip if still processing previous frame
                
                self.is_processing = True
                
                # Process frame
                await self.analyze_frame(frame_info)
                
                self.is_processing = False
                
            except Exception as e:
                logger.error(f"Error in frame processing loop: {e}")
                self.is_processing = False
                await asyncio.sleep(0.1)  # Brief pause before retrying
    
    async def analyze_frame(self, frame_info):
        """Analyze a single frame"""
        try:
            # Decode frame
            frame_data = base64.b64decode(frame_info['frame_data'])
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return
            
            # Save frame temporarily for analysis
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, frame)
                temp_path = tmp_file.name
            
            try:
                # Analyze frame with YOLOv12
                analysis_result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.analyzer.analyze_traffic_scene,
                    temp_path
                )
                
                # Save frame analysis to database
                if self.video_analysis:
                    await self.save_frame_analysis(frame_info, analysis_result)
                
                # Send results to frontend
                await self.send(text_data=json.dumps({
                    'type': 'analysis_result',
                    'data': {
                        'frame_number': frame_info['frame_number'],
                        'timestamp': frame_info['timestamp'],
                        'scene_classification': analysis_result.get('scene_classification', {}),
                        'vehicle_detection': analysis_result.get('vehicle_detection', {}),
                        'traffic_density': analysis_result.get('traffic_density', {}),
                        'traffic_flow': analysis_result.get('traffic_flow', {}),
                        'processing_time': analysis_result.get('processing_time', 0),
                        'fps': analysis_result.get('fps', 0)
                    }
                }))
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            await self.send(text_data=json.dumps({
                'type': 'analysis_error',
                'message': 'Frame analysis failed'
            }))
    
    async def save_frame_analysis(self, frame_info, analysis_result):
        """Save frame analysis results to database"""
        try:
            # Create frame analysis record in MongoDB
            frame_data = {
                'video_analysis_id': str(self.video_analysis['_id']),
                'session_id': self.video_analysis['session_id'],
                'frame_number': frame_info['frame_number'],
                'timestamp': datetime.utcnow(),
                'processing_time': analysis_result.get('processing_time', 0),
                'created_at': datetime.utcnow()
            }
            
            # Set embedded analysis results
            if 'vehicle_detection' in analysis_result:
                vd = analysis_result['vehicle_detection']
                frame_data['vehicle_detection'] = {
                    'cars': vd.get('cars', 0),
                    'motorcycles': vd.get('motorcycles', 0),
                    'buses': vd.get('buses', 0),
                    'trucks': vd.get('trucks', 0),
                    'total_vehicles': vd.get('total_vehicles', 0),
                    'confidence_scores': vd.get('confidence_scores', []),
                    'bounding_boxes': vd.get('bounding_boxes', []),
                    'detection_method': vd.get('detection_method', 'YOLOv12')
                }
            
            if 'scene_classification' in analysis_result:
                sc = analysis_result['scene_classification']
                frame_data['scene_classification'] = {
                    'scene_type': sc.get('scene_type', 'Unknown'),
                    'confidence': sc.get('confidence', 0.0),
                    'all_scores': sc.get('all_scores', {})
                }
            
            if 'traffic_density' in analysis_result:
                td = analysis_result['traffic_density']
                frame_data['traffic_density'] = {
                    'density_level': td.get('density_level', 'Unknown'),
                    'density_score': td.get('density_score', 0.0),
                    'normalized_density': td.get('normalized_density', 0.0)
                }
            
            if 'traffic_flow' in analysis_result:
                tf = analysis_result['traffic_flow']
                frame_data['traffic_flow'] = {
                    'flow_status': tf.get('flow_status', 'Unknown'),
                    'congestion_index': tf.get('congestion_index', 0.0)
                }
            
            await database_sync_to_async(frame_analyses.insert_one)(frame_data)
            
        except Exception as e:
            logger.error(f"Failed to save frame analysis: {e}")
    
    async def end_video_session(self):
        """End the current video analysis session"""
        if not self.video_analysis:
            return
        
        try:
            # Update session end time
            end_time = datetime.utcnow()
            start_time = self.video_analysis.get('start_time', end_time)
            duration = (end_time - start_time).total_seconds()
            
            # Calculate session statistics
            frames = await database_sync_to_async(
                lambda: list(frame_analyses.find({'session_id': self.video_analysis['session_id']}))
            )()
            
            update_data = {
                'end_time': end_time,
                'duration': duration,
                'status': 'completed'
            }
            
            if frames:
                update_data['total_frames_processed'] = len(frames)
                
                # Calculate averages
                processing_times = [f.get('processing_time', 0) for f in frames if f.get('processing_time')]
                if processing_times:
                    update_data['average_processing_time'] = sum(processing_times) / len(processing_times)
                
                # Calculate vehicle statistics
                vehicle_counts = [
                    f.get('vehicle_detection', {}).get('total_vehicles', 0)
                    for f in frames 
                    if f.get('vehicle_detection')
                ]
                if vehicle_counts:
                    update_data['max_vehicles_detected'] = max(vehicle_counts)
                    update_data['min_vehicles_detected'] = min(vehicle_counts)
                    update_data['average_vehicles'] = sum(vehicle_counts) / len(vehicle_counts)
            
            await database_sync_to_async(video_analyses.update_one)(
                {'_id': self.video_analysis['_id']},
                {'$set': update_data}
            )
            
            await self.send(text_data=json.dumps({
                'type': 'session_ended',
                'session_id': self.video_analysis['session_id'],
                'statistics': {
                    'duration': duration,
                    'frames_processed': update_data.get('total_frames_processed', 0),
                    'average_processing_time': update_data.get('average_processing_time', 0),
                    'max_vehicles': update_data.get('max_vehicles_detected', 0),
                    'min_vehicles': update_data.get('min_vehicles_detected', 0),
                    'average_vehicles': update_data.get('average_vehicles', 0)
                }
            }))
            
            logger.info(f"Ended video session: {self.video_analysis['session_id']}")
            
        except Exception as e:
            logger.error(f"Failed to end video session: {e}")
        finally:
            self.video_analysis = None
    
    @database_sync_to_async
    def get_user(self):
        """Get user from WebSocket scope"""
        try:
            user_data = self.scope.get('user')
            if user_data and hasattr(user_data, 'id'):
                # Convert Django user to dict for MongoDB compatibility
                return {
                    'id': str(user_data.id),
                    '_id': str(user_data.id),
                    'username': user_data.username,
                    'email': user_data.email
                }
            return None
        except:
            return None