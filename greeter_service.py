"""
Async gRPC service implementation with Prometheus metrics.
"""
import asyncio
import time
from typing import AsyncIterator

import grpc
from service_pb2 import HelloRequest, HelloReply
from service_pb2_grpc import GreeterServicer
from metrics import metrics


class AsyncGreeterService(GreeterServicer):
    """Async implementation of the Greeter service."""
    
    async def SayHello(self, request: HelloRequest, context: grpc.aio.ServicerContext) -> HelloReply:
        """Handle unary RPC call."""
        try:
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            message = f"Hello, {request.name}!"
            timestamp = int(time.time() * 1000)  # milliseconds
            
            return HelloReply(message=message, timestamp=timestamp)
            
        except Exception as e:
            # Let the interceptor handle metrics
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, f"Error processing request: {str(e)}")
    
    async def SayHelloStream(self, request: HelloRequest, context: grpc.aio.ServicerContext) -> AsyncIterator[HelloReply]:
        """Handle server streaming RPC call."""
        try:
            for i in range(5):
                # Check if client disconnected
                if await context.is_cancelled():
                    break
                
                message = f"Hello {request.name}, message {i+1}!"
                timestamp = int(time.time() * 1000)
                
                yield HelloReply(message=message, timestamp=timestamp)
                
                # Simulate processing time
                await asyncio.sleep(0.5)
                
        except Exception as e:
            # Let the interceptor handle metrics
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, f"Error in streaming: {str(e)}")
    
    async def ProcessRequests(self, request_iterator: AsyncIterator[HelloRequest], context: grpc.aio.ServicerContext) -> HelloReply:
        """Handle client streaming RPC call."""
        try:
            names = []
            async for request in request_iterator:
                names.append(request.name)
                # Simulate processing time
                await asyncio.sleep(0.1)
            
            if not names:
                raise grpc.RpcError(grpc.StatusCode.INVALID_ARGUMENT, "No names provided")
            
            message = f"Processed {len(names)} requests for: {', '.join(names)}"
            timestamp = int(time.time() * 1000)
            
            return HelloReply(message=message, timestamp=timestamp)
            
        except grpc.RpcError:
            # Re-raise gRPC errors as-is
            raise
        except Exception as e:
            # Let the interceptor handle metrics
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, f"Error processing requests: {str(e)}")
