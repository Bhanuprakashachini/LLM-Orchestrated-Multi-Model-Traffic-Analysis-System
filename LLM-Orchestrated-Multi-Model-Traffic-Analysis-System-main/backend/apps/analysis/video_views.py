"""
Video serving views with proper CORS headers
"""
import os
import re
import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class VideoServeView(View):
    """
    Custom video serving view with proper CORS headers
    """
    
    def get(self, request, video_path):
        """Serve video files with proper headers for browser playback"""
        try:
            # Construct full file path
            full_path = os.path.join(settings.MEDIA_ROOT, video_path)
            
            # Security check - ensure path is within MEDIA_ROOT
            if not os.path.abspath(full_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
                logger.warning(f"Attempted path traversal: {video_path}")
                raise Http404("File not found")
            
            # Check if file exists
            if not os.path.exists(full_path):
                logger.warning(f"Video file not found: {full_path}")
                raise Http404("Video file not found")
            
            # Get file info
            file_size = os.path.getsize(full_path)
            content_type, _ = mimetypes.guess_type(full_path)
            
            if not content_type:
                content_type = 'video/mp4'  # Default for video files
            
            logger.info(f"Serving video: {video_path} ({file_size} bytes, {content_type})")
            
            # Handle range requests for video streaming
            range_header = request.META.get('HTTP_RANGE')
            
            if range_header:
                # Parse range header
                range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
                if range_match:
                    start = int(range_match.group(1))
                    end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                    
                    # Ensure valid range
                    start = max(0, min(start, file_size - 1))
                    end = max(start, min(end, file_size - 1))
                    
                    # Create partial content response
                    with open(full_path, 'rb') as f:
                        f.seek(start)
                        data = f.read(end - start + 1)
                    
                    response = HttpResponse(
                        data,
                        status=206,  # Partial Content
                        content_type=content_type
                    )
                    response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                    response['Content-Length'] = str(end - start + 1)
                    response['Accept-Ranges'] = 'bytes'
                else:
                    # Invalid range, serve full file
                    response = FileResponse(
                        open(full_path, 'rb'),
                        content_type=content_type,
                        as_attachment=False
                    )
            else:
                # Serve full file
                response = FileResponse(
                    open(full_path, 'rb'),
                    content_type=content_type,
                    as_attachment=False
                )
                response['Accept-Ranges'] = 'bytes'
            
            # Add CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Range'
            response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range, Accept-Ranges'
            
            # Add caching headers
            response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            
            # Add content disposition for better browser handling
            filename = os.path.basename(full_path)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error serving video {video_path}: {e}")
            raise Http404("Error serving video file")
    
    def head(self, request, video_path):
        """Handle HEAD requests for video files"""
        try:
            # Construct full file path
            full_path = os.path.join(settings.MEDIA_ROOT, video_path)
            
            # Security check
            if not os.path.abspath(full_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
                raise Http404("File not found")
            
            # Check if file exists
            if not os.path.exists(full_path):
                raise Http404("Video file not found")
            
            # Get file info
            file_size = os.path.getsize(full_path)
            content_type, _ = mimetypes.guess_type(full_path)
            
            if not content_type:
                content_type = 'video/mp4'
            
            # Create HEAD response
            response = HttpResponse(content_type=content_type)
            response['Content-Length'] = str(file_size)
            
            # Add CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization'
            
            # Add content disposition
            filename = os.path.basename(full_path)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling HEAD request for video {video_path}: {e}")
            raise Http404("Error accessing video file")
    
    def options(self, request, video_path):
        """Handle OPTIONS requests for CORS preflight"""
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization'
        response['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response

@csrf_exempt
@require_http_methods(["GET", "HEAD", "OPTIONS"])
def serve_annotated_video(request, video_filename):
    """
    Serve annotated videos with proper CORS headers
    """
    video_path = f"uploads/videos/annotated/{video_filename}"
    view = VideoServeView()
    
    if request.method == 'GET':
        return view.get(request, video_path)
    elif request.method == 'HEAD':
        return view.head(request, video_path)
    elif request.method == 'OPTIONS':
        return view.options(request, video_path)