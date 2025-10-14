"""
Simple test script to verify metrics collection works.
"""
import asyncio
import aiohttp
import time

async def test_metrics_endpoint():
    """Test that the metrics endpoint is working."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/metrics') as response:
                if response.status == 200:
                    metrics_text = await response.text()
                    print("✅ Metrics endpoint is working!")
                    print(f"Response length: {len(metrics_text)} characters")
                    
                    # Check for key metrics
                    if 'grpc_requests_total' in metrics_text:
                        print("✅ gRPC request metrics found")
                    if 'grpc_request_duration_seconds' in metrics_text:
                        print("✅ gRPC duration metrics found")
                    if 'grpc_errors_total' in metrics_text:
                        print("✅ gRPC error metrics found")
                    if 'grpc_active_connections' in metrics_text:
                        print("✅ gRPC connection metrics found")
                    
                    return True
                else:
                    print(f"❌ Metrics endpoint returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Failed to connect to metrics endpoint: {e}")
        return False

async def main():
    """Test the metrics endpoint."""
    print("Testing Prometheus metrics endpoint...")
    print("Make sure the server is running (python server.py)")
    print("-" * 50)
    
    # Wait a bit for server to start if it's just starting
    await asyncio.sleep(2)
    
    success = await test_metrics_endpoint()
    
    if success:
        print("\n🎉 All metrics tests passed!")
        print("You can now:")
        print("1. View metrics at: http://localhost:8000/metrics")
        print("2. Run the client: python client.py")
        print("3. Use Docker: docker-compose up")
    else:
        print("\n❌ Metrics tests failed!")
        print("Make sure the server is running: python server.py")

if __name__ == "__main__":
    asyncio.run(main())
