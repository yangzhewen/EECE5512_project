#!/usr/bin/env python3
"""
Caddy-style HTTP/HTTPS server for network measurement
Simple, powerful, and easy to configure web server
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os
import json
import argparse
from datetime import datetime
import mimetypes
import urllib.parse

class CaddyHandler(SimpleHTTPRequestHandler):
    """Enhanced HTTP request handler with logging and CORS support"""
    
    def __init__(self, *args, directory=None, enable_cors=True, **kwargs):
        self.enable_cors = enable_cors
        if directory is None:
            directory = os.getcwd()
        super().__init__(*args, directory=directory, **kwargs)
    
    def end_headers(self):
        """Add CORS headers if enabled"""
        if self.enable_cors:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Enhanced GET handler with custom routes"""
        # Status endpoint
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'server': 'Caddy-style Python Server'
            }
            self.wfile.write(json.dumps(status, indent=2).encode())
            return
        
        # Health check endpoint
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return
        
        # File browser endpoint
        if self.path == '/browse' or self.path.startswith('/browse/'):
            path = self.path.replace('/browse', '', 1) or '/'
            return self.list_directory(path)
        
        # Default file serving
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/upload':
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'No content')
                return
            
            # Read the posted data
            post_data = self.rfile.read(content_length)
            
            # Get filename from headers or use default
            filename = self.headers.get('X-Filename', 'upload_' + str(int(datetime.now().timestamp())))
            filepath = os.path.join(self.directory, filename)
            
            # Save file
            try:
                with open(filepath, 'wb') as f:
                    f.write(post_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'success': True,
                    'filename': filename,
                    'size': content_length
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
            return
        
        # Default: method not allowed
        self.send_response(405)
        self.end_headers()

class CaddyServer:
    """Caddy-style server implementation"""
    
    def __init__(self, host='0.0.0.0', port=8080, directory=None, 
                 enable_https=False, cert_file=None, key_file=None,
                 enable_cors=True):
        self.host = host
        self.port = port
        self.directory = directory or os.getcwd()
        self.enable_https = enable_https
        self.cert_file = cert_file
        self.key_file = key_file
        self.enable_cors = enable_cors
        self.server = None
    
    def create_handler(self):
        """Create request handler with custom settings"""
        def handler(*args, **kwargs):
            return CaddyHandler(*args, directory=self.directory, 
                              enable_cors=self.enable_cors, **kwargs)
        return handler
    
    def start(self):
        """Start the server"""
        handler = self.create_handler()
        self.server = HTTPServer((self.host, self.port), handler)
        
        # Setup HTTPS if enabled
        if self.enable_https:
            if not self.cert_file or not self.key_file:
                print("Error: HTTPS enabled but certificate files not provided")
                return
            
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            try:
                context.load_cert_chain(self.cert_file, self.key_file)
                self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
                protocol = "HTTPS"
            except Exception as e:
                print(f"Error loading SSL certificates: {e}")
                return
        else:
            protocol = "HTTP"
        
        print("=" * 60)
        print(f"Caddy-style Server Starting")
        print(f"Protocol: {protocol}")
        print(f"Address: {self.host}:{self.port}")
        print(f"Directory: {os.path.abspath(self.directory)}")
        print(f"CORS: {'Enabled' if self.enable_cors else 'Disabled'}")
        print("=" * 60)
        print(f"\nServer running at {protocol.lower()}://{self.host}:{self.port}/")
        print(f"Status endpoint: {protocol.lower()}://{self.host}:{self.port}/status")
        print(f"Health check: {protocol.lower()}://{self.host}:{self.port}/health")
        print(f"File browser: {protocol.lower()}://{self.host}:{self.port}/browse")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            self.stop()
    
    def stop(self):
        """Stop the server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Server stopped.")

def main():
    parser = argparse.ArgumentParser(description='Caddy-style HTTP/HTTPS Server')
    parser.add_argument('-H', '--host', default='0.0.0.0', 
                       help='Host address to bind (default: 0.0.0.0)')
    parser.add_argument('-p', '--port', type=int, default=8080,
                       help='Port to listen on (default: 8080)')
    parser.add_argument('-d', '--directory', default=None,
                       help='Directory to serve (default: current directory)')
    parser.add_argument('--https', action='store_true',
                       help='Enable HTTPS')
    parser.add_argument('--cert', help='SSL certificate file')
    parser.add_argument('--key', help='SSL private key file')
    parser.add_argument('--no-cors', action='store_true',
                       help='Disable CORS headers')
    
    args = parser.parse_args()
    
    # Validate HTTPS settings
    if args.https and (not args.cert or not args.key):
        print("Error: --cert and --key are required when --https is enabled")
        return
    
    server = CaddyServer(
        host=args.host,
        port=args.port,
        directory=args.directory,
        enable_https=args.https,
        cert_file=args.cert,
        key_file=args.key,
        enable_cors=not args.no_cors
    )
    
    server.start()

if __name__ == '__main__':
    main()
