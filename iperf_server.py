#!/usr/bin/env python3
"""
iPerf3-compatible server implementation
Full-featured network bandwidth measurement server
"""

import socket
import threading
import json
import time
import struct
import argparse
from datetime import datetime

class iPerfServer:
    """iPerf3-compatible server"""
    
    # iPerf3 protocol constants
    TEST_START = 1
    TEST_RUNNING = 2
    TEST_END = 4
    PARAM_EXCHANGE = 9
    CREATE_STREAMS = 10
    SERVER_TERMINATE = 11
    ACCESS_DENIED = -1
    SERVER_ERROR = -2
    
    def __init__(self, host='0.0.0.0', port=5201, buffer_size=128*1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.running = False
        self.clients = {}
        self.test_id = 0
        
    def handle_control_connection(self, conn, addr):
        """Handle iPerf3 control connection"""
        client_id = f"{addr[0]}:{addr[1]}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Control connection from {client_id}")
        
        try:
            # Receive test parameters
            data = conn.recv(4096)
            if not data:
                return
            
            # Parse JSON parameters (simplified)
            try:
                params = json.loads(data.decode())
                print(f"  Test parameters: {json.dumps(params, indent=2)}")
            except:
                params = {}
            
            # Send acknowledgment
            response = {
                'version': '3.9',
                'system': 'Python iPerf Server',
                'timestamp': int(time.time())
            }
            conn.sendall(json.dumps(response).encode() + b'\n')
            
            # Create test session
            self.test_id += 1
            test_session = {
                'id': self.test_id,
                'client': client_id,
                'start_time': time.time(),
                'params': params,
                'results': []
            }
            self.clients[client_id] = test_session
            
            # Wait for data connections
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error handling control connection: {e}")
        finally:
            conn.close()
    
    def handle_data_connection(self, conn, addr):
        """Handle iPerf3 data connection"""
        client_id = f"{addr[0]}:{addr[1]}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Data connection from {client_id}")
        
        start_time = time.time()
        total_bytes = 0
        interval_bytes = 0
        last_report = start_time
        
        try:
            while self.running:
                data = conn.recv(self.buffer_size)
                if not data:
                    break
                
                total_bytes += len(data)
                interval_bytes += len(data)
                
                # Report every second
                current_time = time.time()
                if current_time - last_report >= 1.0:
                    elapsed = current_time - last_report
                    throughput = (interval_bytes * 8) / (elapsed * 1000000)  # Mbps
                    
                    print(f"  [{client_id}] {interval_bytes / (1024*1024):.2f} MB/s, {throughput:.2f} Mbps")
                    
                    # Store result
                    if client_id in self.clients:
                        self.clients[client_id]['results'].append({
                            'timestamp': current_time,
                            'bytes': interval_bytes,
                            'throughput_mbps': throughput
                        })
                    
                    interval_bytes = 0
                    last_report = current_time
        
        except Exception as e:
            print(f"Error handling data connection: {e}")
        
        finally:
            end_time = time.time()
            total_time = end_time - start_time
            avg_throughput = (total_bytes * 8) / (total_time * 1000000) if total_time > 0 else 0
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Data connection {client_id} closed")
            print(f"  Total: {total_bytes / (1024*1024):.2f} MB in {total_time:.2f}s")
            print(f"  Average: {avg_throughput:.2f} Mbps\n")
            
            # Send final results back
            try:
                results = {
                    'end': True,
                    'bytes': total_bytes,
                    'duration': total_time,
                    'bits_per_second': avg_throughput * 1000000
                }
                conn.sendall(json.dumps(results).encode() + b'\n')
            except:
                pass
            
            conn.close()
    
    def tcp_server(self):
        """Main TCP server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        server_socket.settimeout(1.0)
        
        print(f"iPerf Server listening on {self.host}:{self.port}")
        
        connection_count = 0
        
        while self.running:
            try:
                conn, addr = server_socket.accept()
                connection_count += 1
                
                # First connection is control, subsequent are data
                if connection_count % 2 == 1:
                    # Control connection
                    thread = threading.Thread(
                        target=self.handle_control_connection,
                        args=(conn, addr)
                    )
                else:
                    # Data connection
                    thread = threading.Thread(
                        target=self.handle_data_connection,
                        args=(conn, addr)
                    )
                
                thread.daemon = True
                thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
        
        server_socket.close()
    
    def udp_server(self):
        """UDP server for iPerf"""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((self.host, self.port))
        udp_socket.settimeout(1.0)
        
        print(f"iPerf UDP Server listening on {self.host}:{self.port}")
        
        clients = {}
        
        while self.running:
            try:
                data, addr = udp_socket.recvfrom(65535)
                current_time = time.time()
                
                client_key = f"{addr[0]}:{addr[1]}"
                
                if client_key not in clients:
                    clients[client_key] = {
                        'start_time': current_time,
                        'total_bytes': 0,
                        'total_packets': 0,
                        'last_report': current_time,
                        'interval_bytes': 0,
                        'interval_packets': 0
                    }
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New UDP client: {client_key}")
                
                client = clients[client_key]
                client['total_bytes'] += len(data)
                client['total_packets'] += 1
                client['interval_bytes'] += len(data)
                client['interval_packets'] += 1
                
                # Report every second
                if current_time - client['last_report'] >= 1.0:
                    elapsed = current_time - client['last_report']
                    throughput = (client['interval_bytes'] * 8) / (elapsed * 1000000)  # Mbps
                    
                    print(f"  [{client_key}] {client['interval_packets']} packets, {throughput:.2f} Mbps")
                    
                    client['interval_bytes'] = 0
                    client['interval_packets'] = 0
                    client['last_report'] = current_time
                
            except socket.timeout:
                # Check for timed out clients
                current_time = time.time()
                for key in list(clients.keys()):
                    if current_time - clients[key]['last_report'] > 5.0:
                        client = clients[key]
                        total_time = current_time - client['start_time']
                        avg_throughput = (client['total_bytes'] * 8) / (total_time * 1000000) if total_time > 0 else 0
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] UDP client {key} timed out")
                        print(f"  Total: {client['total_packets']} packets, {client['total_bytes'] / (1024*1024):.2f} MB")
                        print(f"  Average: {avg_throughput:.2f} Mbps\n")
                        
                        del clients[key]
                        
            except Exception as e:
                if self.running:
                    print(f"UDP server error: {e}")
        
        udp_socket.close()
    
    def start(self, mode='tcp'):
        """Start the server"""
        self.running = True
        
        print("=" * 60)
        print("iPerf3-compatible Server")
        print(f"Mode: {mode.upper()}")
        print(f"Listening on {self.host}:{self.port}")
        print("=" * 60 + "\n")
        
        if mode == 'tcp':
            self.tcp_server()
        elif mode == 'udp':
            self.udp_server()
        else:
            print(f"Unknown mode: {mode}")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        time.sleep(1.5)
        print("Server stopped.")

def main():
    parser = argparse.ArgumentParser(description='iPerf3-compatible Server')
    parser.add_argument('-p', '--port', type=int, default=5201,
                       help='Server port (default: 5201)')
    parser.add_argument('-H', '--host', default='0.0.0.0',
                       help='Bind address (default: 0.0.0.0)')
    parser.add_argument('-u', '--udp', action='store_true',
                       help='Use UDP mode')
    
    args = parser.parse_args()
    
    server = iPerfServer(args.host, args.port)
    
    try:
        mode = 'udp' if args.udp else 'tcp'
        server.start(mode)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.stop()

if __name__ == '__main__':
    main()
