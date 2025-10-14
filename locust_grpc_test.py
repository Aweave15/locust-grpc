"""
Locust-based gRPC load testing for distributed Kubernetes deployment.
"""
import random
import time
from typing import Dict, Any

import grpc
from locust import User, task, events
from locust.exception import RescheduleTask
from service_pb2 import HelloRequest
from service_pb2_grpc import GreeterStub


class GRPCLocustUser(User):
    """Locust user class for gRPC load testing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = None
        self.stub = None
        self._connect()
    
    def _connect(self):
        """Connect to gRPC service."""
        try:
            # In Kubernetes, this would be the service name
            endpoint = self.host or "localhost:50051"
            self.channel = grpc.insecure_channel(endpoint)
            self.stub = GreeterStub(self.channel)
        except Exception as e:
            events.request.fire(
                request_type="grpc_connect",
                name="connection",
                response_time=0,
                response_length=0,
                exception=e
            )
            raise RescheduleTask()
    
    def on_start(self):
        """Called when a user starts."""
        self._connect()
    
    def on_stop(self):
        """Called when a user stops."""
        if self.channel:
            self.channel.close()
    
    @task(3)
    def unary_call(self):
        """Test unary gRPC calls (weight: 3)."""
        start_time = time.time()
        
        try:
            name = f"User-{random.randint(1, 1000)}"
            request = HelloRequest(name=name)
            response = self.stub.SayHello(request)
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            events.request.fire(
                request_type="grpc_unary",
                name="SayHello",
                response_time=response_time,
                response_length=len(response.message),
                response=None
            )
            
        except grpc.RpcError as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="grpc_unary",
                name="SayHello",
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            # Reconnect on error
            self._reconnect()
            raise RescheduleTask()
    
    @task(1)
    def server_streaming_call(self):
        """Test server streaming gRPC calls (weight: 1)."""
        start_time = time.time()
        total_messages = 0
        
        try:
            name = f"StreamUser-{random.randint(1, 1000)}"
            request = HelloRequest(name=name)
            
            for response in self.stub.SayHelloStream(request):
                total_messages += 1
                # Simulate processing time
                time.sleep(0.1)
            
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="grpc_streaming",
                name="SayHelloStream",
                response_time=response_time,
                response_length=total_messages,
                response=None
            )
            
        except grpc.RpcError as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="grpc_streaming",
                name="SayHelloStream",
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            self._reconnect()
            raise RescheduleTask()
    
    @task(1)
    def client_streaming_call(self):
        """Test client streaming gRPC calls (weight: 1)."""
        start_time = time.time()
        
        try:
            names = [f"ClientUser-{i}" for i in range(random.randint(2, 5))]
            
            def request_generator():
                for name in names:
                    yield HelloRequest(name=name)
                    time.sleep(0.1)
            
            response = self.stub.ProcessRequests(request_generator())
            
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="grpc_client_streaming",
                name="ProcessRequests",
                response_time=response_time,
                response_length=len(response.message),
                response=None
            )
            
        except grpc.RpcError as e:
            response_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="grpc_client_streaming",
                name="ProcessRequests",
                response_time=response_time,
                response_length=0,
                exception=e
            )
            
            self._reconnect()
            raise RescheduleTask()
    
    def _reconnect(self):
        """Reconnect to gRPC service."""
        if self.channel:
            self.channel.close()
        self._connect()


class GRPCLoadTestUser(GRPCLocustUser):
    """Specialized user for high-load testing."""
    
    @task(10)
    def high_frequency_calls(self):
        """High-frequency unary calls for load testing."""
        self.unary_call()
    
    @task(1)
    def burst_test(self):
        """Burst of rapid calls."""
        for _ in range(5):
            self.unary_call()
            time.sleep(0.01)  # Very short delay


# Custom event handlers for better monitoring
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Custom request event handler."""
    if exception:
        print(f"❌ {request_type} {name} failed: {exception}")
    else:
        print(f"✅ {request_type} {name}: {response_time:.2f}ms")


@events.user_error.add_listener
def on_user_error(user_instance, exception, tb, **kwargs):
    """Custom user error handler."""
    print(f"❌ User error: {exception}")


# Locust configuration
class WebsiteUser(GRPCLocustUser):
    """Main user class for Locust."""
    wait_time = lambda self: random.uniform(0.1, 0.5)  # Random wait between 100-500ms
    weight = 1


class LoadTestUser(GRPCLoadTestUser):
    """High-load user class."""
    wait_time = lambda self: random.uniform(0.01, 0.1)  # Very short wait
    weight = 2  # Higher weight for more load
