"""
Prometheus metrics collection for gRPC services.
"""
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
import grpc


class GRPCMetrics:
    """Prometheus metrics collector for gRPC services."""
    
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'grpc_requests_total',
            'Total number of gRPC requests',
            ['method', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'grpc_request_duration_seconds',
            'Duration of gRPC requests in seconds',
            ['method'],
            registry=self.registry
        )
        
        # Error metrics
        self.error_count = Counter(
            'grpc_errors_total',
            'Total number of gRPC errors',
            ['method', 'error_type'],
            registry=self.registry
        )
        
        # Active connections
        self.active_connections = Gauge(
            'grpc_active_connections',
            'Number of active gRPC connections',
            registry=self.registry
        )
        
        # Service info
        self.service_info = Info(
            'grpc_service_info',
            'Information about the gRPC service',
            registry=self.registry
        )
        
        # Set service info
        self.service_info.info({
            'service': 'example.Greeter',
            'version': '1.0.0'
        })
    
    def record_request(self, method: str, status: str, duration: float):
        """Record a completed request."""
        self.request_count.labels(method=method, status=status).inc()
        self.request_duration.labels(method=method).observe(duration)
    
    def record_error(self, method: str, error_type: str):
        """Record an error."""
        self.error_count.labels(method=method, error_type=error_type).inc()
    
    def increment_connections(self):
        """Increment active connections."""
        self.active_connections.inc()
    
    def decrement_connections(self):
        """Decrement active connections."""
        self.active_connections.dec()
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry).decode('utf-8')


class GRPCMetricsInterceptor(grpc.aio.ServerInterceptor):
    """gRPC interceptor for collecting metrics."""
    
    def __init__(self, metrics: GRPCMetrics):
        self.metrics = metrics
    
    async def intercept_service(self, continuation, handler_call_details):
        """Intercept service calls to collect metrics."""
        method = handler_call_details.method
        start_time = time.time()
        
        try:
            # Increment active connections
            self.metrics.increment_connections()
            
            # Call the actual service method
            response = await continuation(handler_call_details)
            
            # Record successful request
            duration = time.time() - start_time
            self.metrics.record_request(method, 'success', duration)
            
            return response
            
        except grpc.RpcError as e:
            # Record gRPC error
            duration = time.time() - start_time
            error_type = type(e).__name__
            self.metrics.record_error(method, error_type)
            self.metrics.record_request(method, 'error', duration)
            raise
            
        except Exception as e:
            # Record other errors
            duration = time.time() - start_time
            error_type = type(e).__name__
            self.metrics.record_error(method, error_type)
            self.metrics.record_request(method, 'error', duration)
            raise
            
        finally:
            # Decrement active connections
            self.metrics.decrement_connections()


# Global metrics instance
metrics = GRPCMetrics()
