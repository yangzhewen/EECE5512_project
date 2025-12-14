#!/usr/bin/env python3
"""
Simple video streaming server
Supports HTTP video streaming and bandwidth control
"""

from flask import Flask, Response, send_file, render_template_string
import os
import time
import threading

app = Flask(__name__)

# Configuration
VIDEO_DIR = "./videos"  # Video files directory
CHUNK_SIZE = 1024 * 1024  # 1MB chunks
BANDWIDTH_LIMIT = None  # bytes/sec, None means unlimited

class BandwidthThrottle:
    """Bandwidth throttle controller"""
    def __init__(self, rate_limit=None):
        self.rate_limit = rate_limit  # bytes per second
        self.last_time = time.time()
        self.lock = threading.Lock()
    
    def throttle(self, chunk_size):
        """Throttle based on bandwidth limit"""
        if self.rate_limit is None:
            return
        
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_time
            
            if elapsed > 0:
                current_rate = chunk_size / elapsed
                if current_rate > self.rate_limit:
                    sleep_time = (chunk_size / self.rate_limit) - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            
            self.last_time = time.time()

def generate_video_stream(video_path, bandwidth_limit=None):
    """Generate video stream"""
    throttle = BandwidthThrottle(bandwidth_limit)
    
    with open(video_path, 'rb') as video_file:
        while True:
            chunk = video_file.read(CHUNK_SIZE)
            if not chunk:
                break
            
            throttle.throttle(len(chunk))
            yield chunk

@app.route('/')
def index():
    """Home page - display available videos list"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Video Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 10px 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>Video Server</h1>
        <h2>Available Videos:</h2>
        <ul>
            {% for video in videos %}
            <li>
                <a href="/video/{{ video }}">{{ video }}</a> 
                <a href="/stream/{{ video }}" style="margin-left: 20px;">[Stream]</a>
            </li>
            {% endfor %}
        </ul>
        <p>Server Status: Running</p>
        <p>Bandwidth Limit: {{ bandwidth }}</p>
    </body>
    </html>
    """
    
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)
    
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith(('.mp4', '.webm', '.mkv'))]
    bandwidth_str = f"{BANDWIDTH_LIMIT / (1024*1024):.2f} MB/s" if BANDWIDTH_LIMIT else "Unlimited"
    
    return render_template_string(html, videos=videos, bandwidth=bandwidth_str)

@app.route('/video/<filename>')
def video(filename):
    """Direct video download"""
    video_path = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(video_path):
        return send_file(video_path)
    return "Video not found", 404

@app.route('/stream/<filename>')
def stream(filename):
    """Stream video"""
    video_path = os.path.join(VIDEO_DIR, filename)
    if not os.path.exists(video_path):
        return "Video not found", 404
    
    return Response(
        generate_video_stream(video_path, BANDWIDTH_LIMIT),
        mimetype='video/mp4',
        headers={
            'Content-Disposition': f'inline; filename={filename}',
            'Accept-Ranges': 'bytes'
        }
    )

@app.route('/set_bandwidth/<int:mbps>')
def set_bandwidth(mbps):
    """Dynamically set bandwidth limit (MB/s)"""
    global BANDWIDTH_LIMIT
    BANDWIDTH_LIMIT = mbps * 1024 * 1024 if mbps > 0 else None
    return f"Bandwidth limit set to: {mbps} MB/s" if mbps > 0 else "Bandwidth limit removed"

if __name__ == '__main__':
    print("=" * 50)
    print("Video Server Starting...")
    print(f"Video Directory: {os.path.abspath(VIDEO_DIR)}")
    print(f"Bandwidth Limit: {'Unlimited' if BANDWIDTH_LIMIT is None else f'{BANDWIDTH_LIMIT/(1024*1024):.2f} MB/s'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
