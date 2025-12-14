#!/usr/bin/env python3
"""
iPerf3-compatible client implementation
Full-featured network bandwidth measurement client
"""

import socket
import time
import json
import argparse
from datetime import datetime
import threading

class iPerfClient:
    """iPerf3-compatible client"""
    
    def __init__(self, host, port=5201, duration=10, parallel=1, 
                 buffer_size=128*1024, protocol='tcp'):
        self.host = host
        self.port = port
        self.duration = duration
        self.parallel = parallel
        self.buffer_size = buffer_size
        self.protocol = protocol.lower()
        self.results = []
        self.running = False
        
    def send_parameters(self, control_sock):
        """Send test parameters to server"""
        params = {
            'tcp': self.protocol == 'tcp',
            'udp': self.protocol == 'udp',
            'omit': 0,
            'time': self.duration,
            'parallel': self.parallel,
            'len': self.buffer_size,
            'client_version': '3.9'
        }
        
        try:
            control_sock.sendall(json.dumps(params).encode() + b'\n')
            # Receive acknowledgment
            response = control_sock.recv(4096)
            if response:
                print(f"Server response: {response.decode().strip()}")
            return True
        except Exception as e:
            print(f"Error sending parameters: {e}")
            return False
    
    def tcp_stream(self, stream_id):
        """Single TCP stream"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            data = b'X' * self.buffer_size
            start_time = time.time()
            total_bytes = 0
            interval_bytes = 0
            last_report = start_time
            
            stream_results = []
            
            while self.running and (time.time() - start_time) < self.duration:
                try:
                    sent = sock.send(data)
                    total_bytes += sent
                    interval_bytes += sent
                    
                    # Report every second
                    current_time = time.time()
                    if current_time - last_report >= 1.0:
                        elapsed = current_time - last_report
                        throughput = (interval_bytes * 8) / (elapsed * 1000000)  # Mbps
                        
                        result = {
                            'timestamp': current_time,
                            'stream': stream_id,
                            'elapsed': current_time - start_time,
                            'bytes': interval_bytes,
                            'throughput_mbps': throughput
                        }
                        stream_results.append(result)
                        
                        print(f"  [Stream {stream_id}] {interval_bytes / (1024*1024):.2f} MB/s, {throughput:.2f} Mbps")
                        
                        interval_bytes = 0
                        last_report = current_time
                        
                except socket.error as e:
                    print(f"Stream {stream_id} error: {e}")
                    break
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_throughput = (total_bytes * 8) / (total_time * 1000000) if total_time > 0 else 0
            
            sock.close()
            
            return {
                'stream': stream_id,
                'total_bytes': total_bytes,
                'duration': total_time,
                'avg_throughput_mbps': avg_throughput,
                'intervals': stream_results
            }
            
        except Exception as e:
            print(f"Stream {stream_id} error: {e}")
            return None
    
    def udp_stream(self, stream_id, rate_mbps=10):
        """Single UDP stream"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            packet_size = 1400  # Standard UDP packet size
            data = b'X' * packet_size
            
            # Calculate send interval
            target_bytes_per_sec = (rate_mbps * 1000000) / 8
            packets_per_sec = target_bytes_per_sec / packet_size
            send_interval = 1.0 / packets_per_sec if packets_per_sec > 0 else 0
            
            start_time = time.time()
            total_packets = 0
            total_bytes = 0
            interval_packets = 0
            interval_bytes = 0
            last_report = start_time
            
            stream_results = []
            
            while self.running and (time.time() - start_time) < self.duration:
                send_time = time.time()
                
                try:
                    sock.sendto(data, (self.host, self.port))
                    total_packets += 1
                    total_bytes += packet_size
                    interval_packets += 1
                    interval_bytes += packet_size
                    
                    # Report every second
                    current_time = time.time()
                    if current_time - last_report >= 1.0:
                        elapsed = current_time - last_report
                        throughput = (interval_bytes * 8) / (elapsed * 1000000)  # Mbps
                        
                        result = {
                            'timestamp': current_time,
                            'stream': stream_id,
                            'elapsed': current_time - start_time,
                            'packets': interval_packets,
                            'bytes': interval_bytes,
                            'throughput_mbps': throughput
                        }
                        stream_results.append(result)
                        
                        print(f"  [Stream {stream_id}] {interval_packets} pkts, {throughput:.2f} Mbps")
                        
                        interval_packets = 0
                        interval_bytes = 0
                        last_report = current_time
                    
                    # Rate limiting
                    if send_interval > 0:
                        elapsed = time.time() - send_time
                        sleep_time = send_interval - elapsed
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                            
                except socket.error as e:
                    print(f"Stream {stream_id} error: {e}")
                    break
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_throughput = (total_bytes * 8) / (total_time * 1000000) if total_time > 0 else 0
            
            sock.close()
            
            return {
                'stream': stream_id,
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'duration': total_time,
                'avg_throughput_mbps': avg_throughput,
                'intervals': stream_results
            }
            
        except Exception as e:
            print(f"Stream {stream_id} error: {e}")
            return None
    
    def run(self, udp_rate=10):
        """Run the test"""
        print("\n" + "=" * 60)
        print(f"iPerf3-compatible Client")
        print(f"Connecting to {self.host}:{self.port}")
        print(f"Protocol: {self.protocol.upper()}")
        print(f"Duration: {self.duration} seconds")
        print(f"Parallel streams: {self.parallel}")
        if self.protocol == 'udp':
            print(f"UDP rate: {udp_rate} Mbps per stream")
        print("=" * 60 + "\n")
        
        # Establish control connection
        try:
            control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            control_sock.connect((self.host, self.port))
            
            if not self.send_parameters(control_sock):
                print("Failed to send parameters")
                return None
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Control connection error: {e}")
            return None
        
        # Start test streams
        self.running = True
        threads = []
        stream_results = []
        
        print(f"\nStarting test...")
        start_time = time.time()
        
        for i in range(self.parallel):
            if self.protocol == 'tcp':
                thread = threading.Thread(target=lambda sid: stream_results.append(self.tcp_stream(sid)), args=(i,))
            else:
                thread = threading.Thread(target=lambda sid: stream_results.append(self.udp_stream(sid, udp_rate)), args=(i,))
            
            thread.start()
            threads.append(thread)
            time.sleep(0.1)  # Stagger stream starts
        
        # Wait for all streams to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Calculate aggregate results
        total_bytes = sum(r['total_bytes'] for r in stream_results if r)
        total_time = end_time - start_time
        total_throughput = sum(r['avg_throughput_mbps'] for r in stream_results if r)
        
        print("\n" + "=" * 60)
        print(f"Test Complete")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Total Data: {total_bytes / (1024*1024):.2f} MB")
        print(f"Aggregate Throughput: {total_throughput:.2f} Mbps")
        print("=" * 60 + "\n")
        
        control_sock.close()
        
        return {
            'protocol': self.protocol.upper(),
            'duration': total_time,
            'parallel': self.parallel,
            'total_bytes': total_bytes,
            'aggregate_throughput_mbps': total_throughput,
            'streams': [r for r in stream_results if r]
        }
    
    def stop(self):
        """Stop the test"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='iPerf3-compatible Client')
    parser.add_argument('host', help='Server hostname or IP address')
    parser.add_argument('-p', '--port', type=int, default=5201,
                       help='Server port (default: 5201)')
    parser.add_argument('-t', '--time', type=int, default=10,
                       help='Test duration in seconds (default: 10)')
    parser.add_argument('-P', '--parallel', type=int, default=1,
                       help='Number of parallel streams (default: 1)')
    parser.add_argument('-u', '--udp', action='store_true',
                       help='Use UDP instead of TCP')
    parser.add_argument('-b', '--bandwidth', type=int, default=10,
                       help='UDP bandwidth in Mbps (default: 10)')
    parser.add_argument('-o', '--output', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    protocol = 'udp' if args.udp else 'tcp'
    
    client = iPerfClient(
        args.host,
        args.port,
        args.time,
        args.parallel,
        protocol=protocol
    )
    
    try:
        results = client.run(args.bandwidth)
        
        if results and args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output}")
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        client.stop()

if __name__ == '__main__':
    main()
