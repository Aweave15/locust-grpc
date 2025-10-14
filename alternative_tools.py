"""
Alternative load testing tools for gRPC services.
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import grpc
from service_pb2 import HelloRequest
from service_pb2_grpc import GreeterStub


class K6GRPCTest:
    """
    K6-style load testing for gRPC.
    K6 is excellent for gRPC but requires JavaScript.
    """
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.channel = grpc.insecure_channel(endpoint)
        self.stub = GreeterStub(self.channel)
    
    def run_scenario(self, duration_seconds: int = 60, rps: int = 100):
        """Run a K6-style scenario."""
        print(f"Running K6-style test: {duration_seconds}s at {rps} RPS")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        interval = 1.0 / rps
        
        results = []
        
        while time.time() < end_time:
            request_start = time.time()
            
            try:
                request = HelloRequest(name=f"K6User-{int(time.time())}")
                response = self.stub.SayHello(request)
                
                request_time = (time.time() - request_start) * 1000
                results.append({
                    'success': True,
                    'response_time': request_time,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                request_time = (time.time() - request_start) * 1000
                results.append({
                    'success': False,
                    'response_time': request_time,
                    'error': str(e),
                    'timestamp': time.time()
                })
            
            # Maintain RPS
            elapsed = time.time() - request_start
            if elapsed < interval:
                time.sleep(interval - elapsed)
        
        return self._analyze_results(results)
    
    def _analyze_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze test results."""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            response_times = [r['response_time'] for r in successful]
            return {
                'total_requests': len(results),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'success_rate': len(successful) / len(results) * 100,
                'avg_response_time': statistics.mean(response_times),
                'p95_response_time': statistics.quantiles(response_times, n=20)[18],  # 95th percentile
                'p99_response_time': statistics.quantiles(response_times, n=100)[98],  # 99th percentile
                'min_response_time': min(response_times),
                'max_response_time': max(response_times)
            }
        else:
            return {
                'total_requests': len(results),
                'successful_requests': 0,
                'failed_requests': len(failed),
                'success_rate': 0,
                'errors': [r['error'] for r in failed]
            }


class ArtilleryGRPCTest:
    """
    Artillery-style load testing for gRPC.
    Artillery is great for HTTP but has limited gRPC support.
    """
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.channel = grpc.insecure_channel(endpoint)
        self.stub = GreeterStub(self.channel)
    
    def run_phases(self, phases: List[Dict[str, Any]]):
        """Run Artillery-style phases."""
        print("Running Artillery-style phased test")
        
        all_results = []
        
        for phase in phases:
            duration = phase.get('duration', 60)
            arrival_rate = phase.get('arrivalRate', 10)
            name = phase.get('name', 'unnamed')
            
            print(f"Phase: {name} - {duration}s at {arrival_rate} RPS")
            
            phase_results = self._run_phase(duration, arrival_rate)
            all_results.extend(phase_results)
            
            # Brief pause between phases
            time.sleep(2)
        
        return self._analyze_results(all_results)
    
    def _run_phase(self, duration: int, arrival_rate: int) -> List[Dict]:
        """Run a single phase."""
        start_time = time.time()
        end_time = start_time + duration
        interval = 1.0 / arrival_rate
        
        results = []
        
        while time.time() < end_time:
            request_start = time.time()
            
            try:
                request = HelloRequest(name=f"ArtilleryUser-{int(time.time())}")
                response = self.stub.SayHello(request)
                
                request_time = (time.time() - request_start) * 1000
                results.append({
                    'success': True,
                    'response_time': request_time,
                    'phase': 'current'
                })
                
            except Exception as e:
                request_time = (time.time() - request_start) * 1000
                results.append({
                    'success': False,
                    'response_time': request_time,
                    'error': str(e),
                    'phase': 'current'
                })
            
            # Maintain arrival rate
            elapsed = time.time() - request_start
            if elapsed < interval:
                time.sleep(interval - elapsed)
        
        return results
    
    def _analyze_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze test results (same as K6)."""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            response_times = [r['response_time'] for r in successful]
            return {
                'total_requests': len(results),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'success_rate': len(successful) / len(results) * 100,
                'avg_response_time': statistics.mean(response_times),
                'p95_response_time': statistics.quantiles(response_times, n=20)[18],
                'p99_response_time': statistics.quantiles(response_times, n=100)[98],
                'min_response_time': min(response_times),
                'max_response_time': max(response_times)
            }
        else:
            return {
                'total_requests': len(results),
                'successful_requests': 0,
                'failed_requests': len(failed),
                'success_rate': 0,
                'errors': [r['error'] for r in failed]
            }


class JMeterGRPCTest:
    """
    JMeter-style load testing for gRPC.
    JMeter has good gRPC support but is Java-based.
    """
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.channel = grpc.insecure_channel(endpoint)
        self.stub = GreeterStub(self.channel)
    
    def run_thread_group(self, num_threads: int = 10, duration: int = 60, ramp_up: int = 10):
        """Run JMeter-style thread group."""
        print(f"Running JMeter-style test: {num_threads} threads, {duration}s duration, {ramp_up}s ramp-up")
        
        # Create threads for each thread
        import threading
        threads = []
        all_results = []
        results_lock = threading.Lock()
        
        def thread_worker(thread_id, duration, start_delay):
            # Wait for ramp-up
            if start_delay > 0:
                time.sleep(start_delay)
            
            thread_results = self._run_thread(thread_id, duration, 0)
            
            with results_lock:
                all_results.extend(thread_results)
        
        for i in range(num_threads):
            # Stagger thread starts for ramp-up
            start_delay = (i * ramp_up) / num_threads
            thread = threading.Thread(
                target=thread_worker,
                args=(i, duration, start_delay)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return self._analyze_results(all_results)
    
    async def _run_thread(self, thread_id: int, duration: int, start_delay: float) -> List[Dict]:
        """Run a single thread."""
        # Wait for ramp-up
        if start_delay > 0:
            await asyncio.sleep(start_delay)
        
        start_time = time.time()
        end_time = start_time + duration
        
        results = []
        
        while time.time() < end_time:
            request_start = time.time()
            
            try:
                request = HelloRequest(name=f"JMeterUser-{thread_id}-{int(time.time())}")
                response = await self.stub.SayHello(request)
                
                request_time = (time.time() - request_start) * 1000
                results.append({
                    'success': True,
                    'response_time': request_time,
                    'thread_id': thread_id
                })
                
            except Exception as e:
                request_time = (time.time() - request_start) * 1000
                results.append({
                    'success': False,
                    'response_time': request_time,
                    'error': str(e),
                    'thread_id': thread_id
                })
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        return results
    
    def _analyze_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze test results (same as others)."""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            response_times = [r['response_time'] for r in successful]
            return {
                'total_requests': len(results),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'success_rate': len(successful) / len(results) * 100,
                'avg_response_time': statistics.mean(response_times),
                'p95_response_time': statistics.quantiles(response_times, n=20)[18],
                'p99_response_time': statistics.quantiles(response_times, n=100)[98],
                'min_response_time': min(response_times),
                'max_response_time': max(response_times)
            }
        else:
            return {
                'total_requests': len(results),
                'successful_requests': 0,
                'failed_requests': len(failed),
                'success_rate': 0,
                'errors': [r['error'] for r in failed]
            }


# Example usage
async def main():
    """Example of using alternative tools."""
    endpoint = "localhost:50051"
    
    print("=" * 60)
    print("Alternative Load Testing Tools for gRPC")
    print("=" * 60)
    
    # K6-style test
    print("\n1. K6-style test:")
    k6_test = K6GRPCTest(endpoint)
    k6_results = await k6_test.run_scenario(duration_seconds=30, rps=50)
    print(f"K6 Results: {k6_results}")
    
    # Artillery-style test
    print("\n2. Artillery-style test:")
    artillery_test = ArtilleryGRPCTest(endpoint)
    phases = [
        {'name': 'warmup', 'duration': 10, 'arrivalRate': 10},
        {'name': 'load', 'duration': 20, 'arrivalRate': 50},
        {'name': 'spike', 'duration': 10, 'arrivalRate': 100}
    ]
    artillery_results = await artillery_test.run_phases(phases)
    print(f"Artillery Results: {artillery_results}")
    
    # JMeter-style test
    print("\n3. JMeter-style test:")
    jmeter_test = JMeterGRPCTest(endpoint)
    jmeter_results = await jmeter_test.run_thread_group(num_threads=20, duration=30, ramp_up=5)
    print(f"JMeter Results: {jmeter_results}")


if __name__ == "__main__":
    asyncio.run(main())
