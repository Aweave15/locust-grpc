"""
Main server file for the async gRPC service with Prometheus metrics.
"""
import asyncio
import signal
import sys
from aiohttp import web
import grpc
from concurrent import futures

from service_pb2_grpc import add_GreeterServicer_to_server
from greeter_service import AsyncGreeterService
from metrics import metrics, GRPCMetricsInterceptor


class GRPCServer:
    """Async gRPC server with Prometheus metrics."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 50051, metrics_port: int = 8000):
        self.host = host
        self.port = port
        self.metrics_port = metrics_port
        self.server = None
        self.metrics_server = None
        
    async def start_grpc_server(self):
        """Start the gRPC server."""
        # Create server with metrics interceptor
        self.server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            interceptors=[GRPCMetricsInterceptor(metrics)]
        )
        
        # Add the service
        add_GreeterServicer_to_server(AsyncGreeterService(), self.server)
        
        # Listen on the specified port
        listen_addr = f"{self.host}:{self.port}"
        self.server.add_insecure_port(listen_addr)
        
        # Start the server
        await self.server.start()
        print(f"gRPC server started on {listen_addr}")
        
        # Wait for termination
        await self.server.wait_for_termination()
    
    async def start_metrics_server(self):
        """Start the HTTP server for metrics."""
        async def metrics_handler(request):
            """Handle metrics requests."""
            return web.Response(
                text=metrics.get_metrics(),
                content_type='text/plain; version=0.0.4; charset=utf-8'
            )
        
        app = web.Application()
        app.router.add_get('/metrics', metrics_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.metrics_port)
        await site.start()
        print(f"Metrics server started on http://{self.host}:{self.metrics_port}/metrics")
    
    async def stop(self):
        """Stop both servers."""
        if self.server:
            await self.server.stop(grace=5.0)
            print("gRPC server stopped")
        
        if self.metrics_server:
            await self.metrics_server.cleanup()
            print("Metrics server stopped")
    
    async def run(self):
        """Run both servers concurrently."""
        # Start both servers
        await asyncio.gather(
            self.start_grpc_server(),
            self.start_metrics_server()
        )


async def main():
    """Main entry point."""
    server = GRPCServer()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        asyncio.create_task(server.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
