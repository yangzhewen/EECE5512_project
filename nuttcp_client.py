#!/usr/bin/env python3
"""
Nuttcp Client - Network throughput measurement tool
Similar to iperf, used for measuring TCP/UDP bandwidth
"""

import socket
import time
import threading
import argparse
import json
from datetime import datetime

class NuttcpClient:
    def __init__(self, host, port=5001, duration=10, protocol='tcp', buffer_size=128*1024):
        self.host = host
        self.port = port
        self.duration = duration  # Test duration in seconds
        self.protocol = protocol.lower()
        self.buffer_size = buffer_size
        self.results = []
        self.running = False
        
    def tcp_test(self):
        """TCP bandwidth test"""
        print(f"Connecting to {self.host}:{self.port} (TCP)...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            
            data = b'X' * self.buffer_size
            start_time = time.time()
            total_bytes = 0
            interval_bytes = 0
            last_report = start_time
            
            self.running = True
            
            while self.running and (time.time() - start_time) < self.duration:
                try:
                    sent = sock.send(data)
                    total_bytes += sent
                    interval_bytes += sent
                    
                    # 每秒报告一次
                    current_time = time.time()
                    if current_time - last_report >= 1.0:
                        elapsed = current_time - last_report
                        throughput = (interval_bytes * 8) / (elapsed * 1000000)  # Mbps
                        
                        self.results.append({
                            'timestamp': datetime.now().isoformat(),
                            'elapsed': current_time - start_time,
                            'bytes': interval_bytes,
                            'throughput_mbps': throughput
                        })
                        
                        print(f"[{elapsed:.1f}s] {interval_bytes / (1024*1024):.2f} MB, {throughput:.2f} Mbps")
                        
                        interval_bytes = 0
                        last_report = current_time
                        
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_throughput = (total_bytes * 8) / (total_time * 1000000)  # Mbps
            
            sock.close()
            
            print("\n" + "="*50)
            print(f"TCP Test Complete")
            print(f"Total Time: {total_time:.2f} seconds")
            print(f"Total Data: {total_bytes / (1024*1024):.2f} MB")
            print(f"Average Throughput: {avg_throughput:.2f} Mbps")
            print("="*50)
            
            return {
                'protocol': 'TCP',
                'duration': total_time,
                'total_bytes': total_bytes,
                'avg_throughput_mbps': avg_throughput,
                'intervals': self.results
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def udp_test(self, rate_mbps=10):
        """UDP bandwidth test"""
        print(f"Connecting to {self.host}:{self.port} (UDP)...")
        print(f"Target rate: {rate_mbps} Mbps")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            packet_size = 1400  # Typical UDP packet size
            data = b'X' * packet_size
            
            # Calculate send interval to achieve target rate
            target_bytes_per_sec = (rate_mbps * 1000000) / 8
            packets_per_sec = target_bytes_per_sec / packet_size
            send_interval = 1.0 / packets_per_sec if packets_per_sec > 0 else 0
            
            start_time = time.time()
            total_packets = 0
            total_bytes = 0
            interval_packets = 0
            interval_bytes = 0
            last_report = start_time
            
            self.running = True
            
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
                        
                        self.results.append({
                            'timestamp': datetime.now().isoformat(),
                            'elapsed': current_time - start_time,
                            'packets': interval_packets,
                            'bytes': interval_bytes,
                            'throughput_mbps': throughput
                        })
                        
                        print(f"[{elapsed:.1f}s] {interval_packets} packets, {throughput:.2f} Mbps")
                        
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
                    print(f"Socket error: {e}")
                    break
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_throughput = (total_bytes * 8) / (total_time * 1000000)  # Mbps
            
            sock.close()
            
            print("\n" + "="*50)
            print(f"UDP Test Complete")
            print(f"Total Time: {total_time:.2f} seconds")
            print(f"Total Packets: {total_packets}")
            print(f"Total Data: {total_bytes / (1024*1024):.2f} MB")
            print(f"Average Throughput: {avg_throughput:.2f} Mbps")
            print("="*50)
            
            return {
                'protocol': 'UDP',
                'duration': total_time,
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'avg_throughput_mbps': avg_throughput,
                'intervals': self.results
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def run(self, udp_rate=10):
        """Run test"""
        if self.protocol == 'tcp':
            return self.tcp_test()
        elif self.protocol == 'udp':
            return self.udp_test(udp_rate)
        else:
            print(f"Unknown protocol: {self.protocol}")
            return None
    
    def stop(self):
        """Stop test"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Nuttcp Client - Network Throughput Measurement')
    parser.add_argument('host', help='Server hostname or IP address')
    parser.add_argument('-p', '--port', type=int, default=5001, help='Server port (default: 5001)')
    parser.add_argument('-t', '--time', type=int, default=10, help='Test duration in seconds (default: 10)')
    parser.add_argument('-u', '--udp', action='store_true', help='Use UDP instead of TCP')
    parser.add_argument('-r', '--rate', type=int, default=10, help='UDP target rate in Mbps (default: 10)')
    parser.add_argument('-o', '--output', help='Output JSON file for results')
    
    args = parser.parse_args()
    
    protocol = 'udp' if args.udp else 'tcp'
    
    print(f"\nNuttcp Client - {protocol.upper()} Throughput Test")
    print(f"Target: {args.host}:{args.port}")
    print(f"Duration: {args.time} seconds")
    if args.udp:
        print(f"UDP Rate: {args.rate} Mbps")
    print()
    
    client = NuttcpClient(args.host, args.port, args.time, protocol)
    
    try:
        results = client.run(args.rate)
        
        if results and args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        client.stop()

if __name__ == '__main__':
    main()
