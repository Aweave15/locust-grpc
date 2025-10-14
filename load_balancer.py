"""
gRPC Load Balancer implementation for Kubernetes.
"""
import asyncio
import random
import time
from typing import List, Optional
import grpc
from grpc.aio import Channel
from service_pb2 import HelloRequest
from service_pb2_grpc import GreeterStub


class GRPCLoadBalancer:
    """Simple round-robin load balancer for gRPC services."""
    
    def __init__(self, service_endpoints: List[str]):
        self.endpoints = service_endpoints
        self.current_index = 0
        self.channels: List[Channel] = []
        self.stubs: List[GreeterStub] = []
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize gRPC channels and stubs for all endpoints."""
        for endpoint in self.endpoints:
            channel = grpc.aio.insecure_channel(endpoint)
            stub = GreeterStub(channel)
            self.channels.append(channel)
            self.stubs.append(stub)
    
    def get_next_stub(self) -> GreeterStub:
        """Get next stub using round-robin."""
        stub = self.stubs[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.stubs)
        return stub
    
    def get_random_stub(self) -> GreeterStub:
        """Get random stub for load distribution."""
        return random.choice(self.stubs)
    
    async def say_hello(self, name: str, use_random: bool = False) -> str:
        """Make a load-balanced gRPC call."""
        stub = self.get_random_stub() if use_random else self.get_next_stub()
        
        try:
            request = HelloRequest(name=name)
            response = await stub.SayHello(request)
            return response.message
        except grpc.RpcError as e:
            raise Exception(f"gRPC call failed: {e.code()} - {e.details()}")
    
    async def close(self):
        """Close all channels."""
        for channel in self.channels:
            await channel.close()


class HealthCheckLoadBalancer(GRPCLoadBalancer):
    """Load balancer with health checking."""
    
    def __init__(self, service_endpoints: List[str], health_check_interval: float = 30.0):
        super().__init__(service_endpoints)
        self.healthy_endpoints = set(range(len(self.endpoints)))
        self.health_check_interval = health_check_interval
        self.last_health_check = 0
        self._start_health_checker()
    
    def _start_health_checker(self):
        """Start background health checking."""
        asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Continuously check endpoint health."""
        while True:
            await asyncio.sleep(self.health_check_interval)
            await self._check_all_endpoints()
    
    async def _check_all_endpoints(self):
        """Check health of all endpoints."""
        for i, stub in enumerate(self.stubs):
            try:
                # Simple health check - make a quick request
                request = HelloRequest(name="health_check")
                await asyncio.wait_for(stub.SayHello(request), timeout=5.0)
                self.healthy_endpoints.add(i)
            except Exception:
                self.healthy_endpoints.discard(i)
    
    def get_healthy_stub(self) -> Optional[GreeterStub]:
        """Get a stub from a healthy endpoint."""
        if not self.healthy_endpoints:
            return None
        
        healthy_indices = list(self.healthy_endpoints)
        index = random.choice(healthy_indices)
        return self.stubs[index]
    
    async def say_hello(self, name: str) -> str:
        """Make a load-balanced call to healthy endpoints only."""
        stub = self.get_healthy_stub()
        if not stub:
            raise Exception("No healthy endpoints available")
        
        try:
            request = HelloRequest(name=name)
            response = await stub.SayHello(request)
            return response.message
        except grpc.RpcError as e:
            # Mark endpoint as unhealthy and retry with another
            for i, s in enumerate(self.stubs):
                if s == stub:
                    self.healthy_endpoints.discard(i)
                    break
            
            # Retry with another healthy endpoint
            return await self.say_hello(name)


# Example usage
async def main():
    """Example of using the load balancer."""
    # In Kubernetes, these would be service endpoints
    endpoints = [
        "grpc-service-1:50051",
        "grpc-service-2:50051", 
        "grpc-service-3:50051"
    ]
    
    # Create load balancer
    lb = HealthCheckLoadBalancer(endpoints)
    
    try:
        # Make some load-balanced calls
        for i in range(10):
            response = await lb.say_hello(f"User-{i}")
            print(f"Response {i}: {response}")
            await asyncio.sleep(0.1)
    
    finally:
        await lb.close()


if __name__ == "__main__":
    asyncio.run(main())
