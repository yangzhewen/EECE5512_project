#!/usr/bin/env python3
"""
Nuttcp Server - Network throughput measurement tool server
Receives TCP/UDP data and measures throughput
"""

import socket
import time
import threading
import argparse
from datetime import datetime

class NuttcpServer:
    def __init__(self, host='0.0.0.0', port=5001, buffer_size=128*1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.running = False
        
    def handle_tcp_client(self, client_socket, addr):
        """Handle TCP client connection"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] TCP connection from {addr[0]}:{addr[1]}")
        
        start_time = time.time()
        total_bytes = 0
        interval_bytes = 0
        last_report = start_time
        
        try:
            while self.running:
                data = client_socket.recv(self.buffer_size)
                if not data:
                    break
                
                total_bytes += len(data)
                interval_bytes += len(data)
                
                # Report every second
                current_time = time.time()
                if current_time - last_report >= 1.0:
                    elapsed = current_time - last_report
                    throughput = (interval_bytes * 8) / (elapsed * 1000000)  # Mbps
                    print(f"  [{addr[0]}] {interval_bytes / (1024*1024):.2f} MB/s, {throughput:.2f} Mbps")
                    
                    interval_bytes = 0
                    last_report = current_time
        
        except Exception as e:
            print(f"Error handling TCP client: {e}")
        
        finally:
            end_time = time.time()
            total_time = end_time - start_time
            avg_throughput = (total_bytes * 8) / (total_time * 1000000) if total_time > 0 else 0
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] TCP client {addr[0]}:{addr[1]} disconnected")
            print(f"  Total: {total_bytes / (1024*1024):.2f} MB in {total_time:.2f}s, Avg: {avg_throughput:.2f} Mbps\n")
            
            client_socket.close()
    
    def tcp_server(self):
        """TCP server"""
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind((self.host, self.port))
        tcp_socket.listen(5)
        tcp_socket.settimeout(1.0)
        
        print(f"TCP Server listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, addr = tcp_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_tcp_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"TCP server error: {e}")
        
        tcp_socket.close()
    
    def udp_server(self):
        """UDP server"""
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((self.host, self.port))
        udp_socket.settimeout(1.0)
        
        print(f"UDP Server listening on {self.host}:{self.port}")
        
        clients = {}  # Track client statistics
        
        while self.running:
            try:
                data, addr = udp_socket.recvfrom(65535)
                current_time = time.time()
                
                if addr not in clients:
                    clients[addr] = {
                        'start_time': current_time,
                        'total_bytes': 0,
                        'total_packets': 0,
                        'last_report': current_time,
                        'interval_bytes': 0,
                        'interval_packets': 0
                    }
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New UDP client: {addr[0]}:{addr[1]}")
                
                client = clients[addr]
                client['total_bytes'] += len(data)
                client['total_packets'] += 1
                client['interval_bytes'] += len(data)
                client['interval_packets'] += 1
                
                # Report every second
                if current_time - client['last_report'] >= 1.0:
                    elapsed = current_time - client['last_report']
                    throughput = (client['interval_bytes'] * 8) / (elapsed * 1000000)  # Mbps
                    print(f"  [{addr[0]}:{addr[1]}] {client['interval_packets']} packets, {throughput:.2f} Mbps")
                    
                    client['interval_bytes'] = 0
                    client['interval_packets'] = 0
                    client['last_report'] = current_time
                
            except socket.timeout:
                # Check for timed out clients
                current_time = time.time()
                for addr in list(clients.keys()):
                    if current_time - clients[addr]['last_report'] > 5.0:
                        client = clients[addr]
                        total_time = current_time - client['start_time']
                        avg_throughput = (client['total_bytes'] * 8) / (total_time * 1000000) if total_time > 0 else 0
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] UDP client {addr[0]}:{addr[1]} timed out")
                        print(f"  Total: {client['total_packets']} packets, {client['total_bytes'] / (1024*1024):.2f} MB, Avg: {avg_throughput:.2f} Mbps\n")
                        
                        del clients[addr]
                        
            except Exception as e:
                if self.running:
                    print(f"UDP server error: {e}")
        
        udp_socket.close()
    
    def start(self):
        """Start server"""
        self.running = True
        
        # Start TCP server thread
        tcp_thread = threading.Thread(target=self.tcp_server)
        tcp_thread.daemon = True
        tcp_thread.start()
        
        # Start UDP server thread
        udp_thread = threading.Thread(target=self.udp_server)
        udp_thread.daemon = True
        udp_thread.start()
        
        print("\nNuttcp Server is running. Press Ctrl+C to stop.\n")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            self.stop()
    
    def stop(self):
        """Stop server"""
        self.running = False
        time.sleep(1.5)
        print("Server stopped.")

def main():
    parser = argparse.ArgumentParser(description='Nuttcp Server - Network Throughput Measurement')
    parser.add_argument('-p', '--port', type=int, default=5001, help='Server port (default: 5001)')
    parser.add_argument('-H', '--host', default='0.0.0.0', help='Bind address (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    print("="*50)
    print("Nuttcp Server")
    print(f"Listening on {args.host}:{args.port}")
    print("="*50 + "\n")
    
    server = NuttcpServer(args.host, args.port)
    server.start()

if __name__ == '__main__':
    main()
