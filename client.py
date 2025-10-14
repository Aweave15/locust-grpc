"""
Example async gRPC client for testing the service.
"""
import asyncio
import time

import grpc
from service_pb2 import HelloRequest
from service_pb2_grpc import GreeterStub


class AsyncGRPCClient:
    """Async gRPC client for testing."""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.channel = None
        self.stub = None
    
    async def connect(self):
        """Connect to the gRPC server."""
        self.channel = grpc.aio.insecure_channel(f"{self.host}:{self.port}")
        self.stub = GreeterStub(self.channel)
        print(f"Connected to gRPC server at {self.host}:{self.port}")
    
    async def disconnect(self):
        """Disconnect from the gRPC server."""
        if self.channel:
            await self.channel.close()
            print("Disconnected from gRPC server")
    
    async def test_unary_call(self, name: str = "World"):
        """Test unary RPC call."""
        try:
            request = HelloRequest(name=name)
            response = await self.stub.SayHello(request)
            print(f"Unary call response: {response.message} (timestamp: {response.timestamp})")
            return response
        except grpc.RpcError as e:
            print(f"Unary call failed: {e.code()} - {e.details()}")
            return None
    
    async def test_server_streaming(self, name: str = "Streaming"):
        """Test server streaming RPC call."""
        try:
            request = HelloRequest(name=name)
            print(f"Starting server streaming for {name}...")
            
            async for response in self.stub.SayHelloStream(request):
                print(f"Stream response: {response.message} (timestamp: {response.timestamp})")
            
            print("Server streaming completed")
        except grpc.RpcError as e:
            print(f"Server streaming failed: {e.code()} - {e.details()}")
    
    async def test_client_streaming(self, names: list = None):
        """Test client streaming RPC call."""
        if names is None:
            names = ["Alice", "Bob", "Charlie"]
        
        try:
            print(f"Starting client streaming with names: {names}")
            
            async def request_generator():
                for name in names:
                    yield HelloRequest(name=name)
                    await asyncio.sleep(0.2)  # Simulate delay between requests
            
            response = await self.stub.ProcessRequests(request_generator())
            print(f"Client streaming response: {response.message} (timestamp: {response.timestamp})")
            return response
        except grpc.RpcError as e:
            print(f"Client streaming failed: {e.code()} - {e.details()}")
            return None
    
    async def run_load_test(self, num_requests: int = 10):
        """Run a load test with multiple concurrent requests."""
        print(f"Running load test with {num_requests} concurrent requests...")
        
        start_time = time.time()
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(num_requests):
            task = self.test_unary_call(f"LoadTest-{i}")
            tasks.append(task)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        successful_requests = sum(1 for result in results if result is not None and not isinstance(result, Exception))
        
        print(f"Load test completed:")
        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Failed: {num_requests - successful_requests}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Requests/second: {num_requests / duration:.2f}")


async def main():
    """Main function to run client tests."""
    client = AsyncGRPCClient()
    
    try:
        await client.connect()
        
        print("=" * 50)
        print("Testing gRPC Service with Prometheus Metrics")
        print("=" * 50)
        
        # Test unary call
        print("\n1. Testing unary call...")
        await client.test_unary_call("Alice")
        
        # Test server streaming
        print("\n2. Testing server streaming...")
        await client.test_server_streaming("Bob")
        
        # Test client streaming
        print("\n3. Testing client streaming...")
        await client.test_client_streaming(["Charlie", "David", "Eve"])
        
        # Test error handling
        print("\n4. Testing error handling...")
        await client.test_unary_call("")  # Empty name should cause error
        
        # Run load test
        print("\n5. Running load test...")
        await client.run_load_test(20)
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        print("Check metrics at: http://localhost:8000/metrics")
        print("=" * 50)
        
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
