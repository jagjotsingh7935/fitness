import os
import re
import mimetypes
import urllib.parse
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.conf import settings

def range_media_serve(request, path):
    """
    Serve media files with full HTTP 206 Partial Content (Range request) support.
    Essential for mobile video streaming (ExoPlayer on Android, AVPlayer on iOS),
    allowing seeking, partial buffering, and fast reading of MP4 moov metadata.
    """
    # Unquote repeatedly until stable (handles raw, %20, and %2520 double-encoded URLs)
    unquoted_path = path
    for _ in range(3):
        new_unquoted = urllib.parse.unquote(unquoted_path)
        if new_unquoted == unquoted_path:
            break
        unquoted_path = new_unquoted

    normalized_media_root = os.path.abspath(settings.MEDIA_ROOT)
    full_path = os.path.abspath(os.path.join(normalized_media_root, unquoted_path))

    # Security check: prevent directory traversal outside MEDIA_ROOT
    if not full_path.startswith(normalized_media_root) or not os.path.isfile(full_path):
        raise Http404("Media file not found")

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    content_type = content_type or 'video/mp4'

    # Handle HEAD request
    if request.method == 'HEAD':
        response = HttpResponse(status=200, content_type=content_type)
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    range_header = request.headers.get('Range', request.META.get('HTTP_RANGE', ''))
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header) if range_header else None

    # Handle Range requests (HTTP 206 Partial Content)
    if range_match:
        first_byte = int(range_match.group(1))
        last_byte_str = range_match.group(2)
        last_byte = int(last_byte_str) if last_byte_str else file_size - 1

        if first_byte >= file_size or last_byte >= file_size or first_byte > last_byte:
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{file_size}'
            response['Accept-Ranges'] = 'bytes'
            return response

        length = last_byte - first_byte + 1

        def file_iterator(start, end, chunk_size=65536):
            with open(full_path, 'rb') as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    read_len = min(chunk_size, remaining)
                    data = f.read(read_len)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        response = StreamingHttpResponse(
            file_iterator(first_byte, last_byte),
            status=206,
            content_type=content_type
        )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    # Standard full-content request (HTTP 200 OK)
    def full_iterator(chunk_size=65536):
        with open(full_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                yield chunk

    response = StreamingHttpResponse(
        full_iterator(),
        content_type=content_type
    )
    response['Content-Length'] = str(file_size)
    response['Accept-Ranges'] = 'bytes'
    response['Access-Control-Allow-Origin'] = '*'
    return response
