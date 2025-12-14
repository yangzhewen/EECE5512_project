#!/usr/bin/env python3
"""
Integrated Network Measurement Application
Integrates YouTube video quality monitoring, Nuttcp bandwidth testing and video server
"""

import json
import time
import threading
import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import os

class MeasurementApp:
    def __init__(self, output_dir='./measurements'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.running = False
        self.measurements = []
        
    def run_nuttcp_test(self, server, port=5001, duration=10, protocol='tcp'):
        """Run Nuttcp bandwidth test"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting Nuttcp test ({protocol.upper()})...")
        
        timestamp = int(time.time())
        output_file = self.output_dir / f"nuttcp_{protocol}_{timestamp}.json"
        
        try:
            # Use subprocess to call nuttcp_client
            cmd = [
                'python', 'nuttcp_client.py',
                server,
                '-p', str(port),
                '-t', str(duration),
                '-o', str(output_file)
            ]
            
            if protocol == 'udp':
                cmd.extend(['-u', '-r', '50'])  # 50 Mbps UDP test
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
            
            if result.returncode == 0:
                print(f"Nuttcp test completed. Results saved to: {output_file}")
                
                # Read results
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    return data
            else:
                print(f"Nuttcp test failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Nuttcp test timed out")
            return None
        except Exception as e:
            print(f"Error running Nuttcp test: {e}")
            return None
    
    def parse_youtube_logs(self, log_file):
        """Parse YouTube log file"""
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
            
            # Collect key metrics
            stats = {
                'total_stalls': 0,
                'total_stall_duration': 0,
                'quality_changes': [],
                'avg_quality': None,
                'periodic_samples': 0
            }
            
            qualities = []
            
            for entry in data:
                if entry['type'] == 'stall':
                    stats['total_stalls'] = entry.get('totalStalls', 0)
                    stats['total_stall_duration'] = entry.get('totalStallDuration', 0)
                
                elif entry['type'] == 'quality_change':
                    stats['quality_changes'].append({
                        'timestamp': entry['timestamp'],
                        'quality': entry['quality']
                    })
                
                elif entry['type'] == 'periodic':
                    stats['periodic_samples'] += 1
                    if entry.get('quality'):
                        qualities.append(entry['quality'])
            
            # Calculate average quality
            if qualities:
                # Get most common quality
                from collections import Counter
                quality_counter = Counter(qualities)
                stats['avg_quality'] = quality_counter.most_common(1)[0][0]
            
            return stats
            
        except Exception as e:
            print(f"Error parsing YouTube logs: {e}")
            return None
    
    def run_integrated_test(self, server, duration=60, test_interval=10):
        """
        Run integrated test
        - Monitor YouTube video playback
        - Run Nuttcp tests periodically
        """
        print("="*60)
        print("Starting Integrated Network Measurement")
        print(f"Server: {server}")
        print(f"Test Duration: {duration} seconds")
        print(f"Test Interval: {test_interval} seconds")
        print("="*60 + "\n")
        
        self.running = True
        start_time = time.time()
        
        test_results = {
            'start_time': datetime.now().isoformat(),
            'server': server,
            'duration': duration,
            'nuttcp_tests': [],
            'youtube_stats': None
        }
        
        test_count = 0
        
        try:
            while self.running and (time.time() - start_time) < duration:
                elapsed = time.time() - start_time
                
                # Run Nuttcp test every test_interval
                if elapsed >= test_count * test_interval:
                    test_count += 1
                    
                    print(f"\n--- Test #{test_count} at {elapsed:.1f}s ---")
                    
                    # TCP test
                    tcp_result = self.run_nuttcp_test(server, duration=5, protocol='tcp')
                    if tcp_result:
                        test_results['nuttcp_tests'].append({
                            'test_number': test_count,
                            'elapsed': elapsed,
                            'result': tcp_result
                        })
                    
                    time.sleep(2)
                    
                    # UDP test
                    udp_result = self.run_nuttcp_test(server, duration=5, protocol='udp')
                    if udp_result:
                        test_results['nuttcp_tests'].append({
                            'test_number': test_count,
                            'elapsed': elapsed,
                            'result': udp_result
                        })
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        
        finally:
            self.running = False
            test_results['end_time'] = datetime.now().isoformat()
            test_results['actual_duration'] = time.time() - start_time
            
            # Save comprehensive results
            output_file = self.output_dir / f"integrated_test_{int(start_time)}.json"
            with open(output_file, 'w') as f:
                json.dump(test_results, f, indent=2)
            
            print("\n" + "="*60)
            print("Integrated Test Complete")
            print(f"Total Tests: {test_count}")
            print(f"Results saved to: {output_file}")
            print("="*60)
            
            # Generate summary
            self.generate_summary(test_results)
    
    def generate_summary(self, results):
        """Generate test summary"""
        print("\n--- Test Summary ---")
        
        if results['nuttcp_tests']:
            tcp_tests = [t for t in results['nuttcp_tests'] if t['result']['protocol'] == 'TCP']
            udp_tests = [t for t in results['nuttcp_tests'] if t['result']['protocol'] == 'UDP']
            
            if tcp_tests:
                avg_tcp = sum(t['result']['avg_throughput_mbps'] for t in tcp_tests) / len(tcp_tests)
                print(f"Average TCP Throughput: {avg_tcp:.2f} Mbps ({len(tcp_tests)} tests)")
            
            if udp_tests:
                avg_udp = sum(t['result']['avg_throughput_mbps'] for t in udp_tests) / len(udp_tests)
                print(f"Average UDP Throughput: {avg_udp:.2f} Mbps ({len(udp_tests)} tests)")
        
        if results.get('youtube_stats'):
            yt = results['youtube_stats']
            print(f"\nYouTube Video Quality:")
            print(f"  Total Stalls: {yt['total_stalls']}")
            print(f"  Total Stall Duration: {yt['total_stall_duration']/1000:.2f}s")
            print(f"  Quality Changes: {len(yt['quality_changes'])}")
            print(f"  Average Quality: {yt['avg_quality']}")
    
    def analyze_youtube_log(self, log_file):
        """Analyze single YouTube log file"""
        print(f"\nAnalyzing YouTube log: {log_file}")
        
        stats = self.parse_youtube_logs(log_file)
        
        if stats:
            print("\n--- YouTube Playback Statistics ---")
            print(f"Total Stalls: {stats['total_stalls']}")
            print(f"Total Stall Duration: {stats['total_stall_duration']/1000:.2f} seconds")
            print(f"Quality Changes: {len(stats['quality_changes'])}")
            print(f"Most Common Quality: {stats['avg_quality']}")
            print(f"Periodic Samples: {stats['periodic_samples']}")
            
            if stats['quality_changes']:
                print("\nQuality Change Timeline:")
                for change in stats['quality_changes'][:10]:  # 只显示前10个
                    ts = datetime.fromtimestamp(change['timestamp']/1000).strftime('%H:%M:%S')
                    print(f"  {ts}: {change['quality']}")
            
            return stats
        
        return None

def main():
    parser = argparse.ArgumentParser(description='Integrated Network Measurement Application')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # 集成测试命令
    test_parser = subparsers.add_parser('test', help='Run integrated measurement test')
    test_parser.add_argument('server', help='Nuttcp server address')
    test_parser.add_argument('-d', '--duration', type=int, default=60, help='Test duration in seconds (default: 60)')
    test_parser.add_argument('-i', '--interval', type=int, default=10, help='Test interval in seconds (default: 10)')
    test_parser.add_argument('-o', '--output', default='./measurements', help='Output directory (default: ./measurements)')
    
    # YouTube日志分析命令
    analyze_parser = subparsers.add_parser('analyze', help='Analyze YouTube log file')
    analyze_parser.add_argument('logfile', help='YouTube log JSON file')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        app = MeasurementApp(output_dir=args.output)
        app.run_integrated_test(args.server, args.duration, args.interval)
    
    elif args.command == 'analyze':
        app = MeasurementApp()
        app.analyze_youtube_log(args.logfile)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
