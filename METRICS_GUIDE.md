# Prometheus Metrics for Async gRPC Services

This guide explains how to collect and expose Prometheus metrics in an async Python gRPC service.

## Key Components

### 1. Metrics Collection (`metrics.py`)

The `GRPCMetrics` class provides comprehensive metrics collection:

```python
# Request metrics
request_count = Counter('grpc_requests_total', 'Total gRPC requests', ['method', 'status'])
request_duration = Histogram('grpc_request_duration_seconds', 'Request duration', ['method'])

# Error metrics  
error_count = Counter('grpc_errors_total', 'Total gRPC errors', ['method', 'error_type'])

# Connection metrics
active_connections = Gauge('grpc_active_connections', 'Active connections')
```

### 2. gRPC Interceptor (`GRPCMetricsInterceptor`)

The interceptor automatically collects metrics for all gRPC calls:

```python
class GRPCMetricsInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        # Record start time, increment connections
        # Call the actual service method
        # Record metrics (success/error, duration)
        # Decrement connections
```

### 3. Metrics Exposure

The server exposes metrics via HTTP endpoint:

```python
# HTTP server on port 8000 serves /metrics endpoint
# Prometheus can scrape from http://localhost:8000/metrics
```

## Key Differences from FastAPI

### FastAPI Approach
```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

### gRPC Approach
```python
# 1. Create custom metrics collector
metrics = GRPCMetrics()

# 2. Use gRPC interceptor for automatic collection
interceptor = GRPCMetricsInterceptor(metrics)

# 3. Add interceptor to server
server = grpc.aio.server(interceptors=[interceptor])

# 4. Expose metrics via separate HTTP server
# (gRPC doesn't have built-in HTTP endpoints)
```

## Metrics Collected

### Request Metrics
- `grpc_requests_total{method, status}` - Total requests by method and status
- `grpc_request_duration_seconds{method}` - Request duration histogram

### Error Metrics  
- `grpc_errors_total{method, error_type}` - Errors by method and type

### Connection Metrics
- `grpc_active_connections` - Current active connections

### Service Info
- `grpc_service_info` - Service metadata

## Usage Examples

### Basic Setup
```python
from metrics import metrics, GRPCMetricsInterceptor

# Add interceptor to server
server = grpc.aio.server(interceptors=[GRPCMetricsInterceptor(metrics)])
```

### Custom Metrics
```python
# Add custom business metrics
custom_counter = Counter('business_operations_total', 'Business operations', ['operation_type'])
custom_counter.labels(operation_type='user_creation').inc()
```

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'grpc-service'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
```

## Best Practices

1. **Use Interceptors**: Automatically collect metrics for all gRPC calls
2. **Label Consistently**: Use consistent label names across metrics
3. **Monitor Key Metrics**: Focus on request rate, duration, and error rate
4. **Separate HTTP Server**: gRPC services need separate HTTP server for metrics
5. **Handle Errors Gracefully**: Ensure metrics collection doesn't break service

## Monitoring Queries

### Request Rate
```promql
rate(grpc_requests_total[5m])
```

### Error Rate
```promql
rate(grpc_errors_total[5m]) / rate(grpc_requests_total[5m])
```

### P95 Latency
```promql
histogram_quantile(0.95, rate(grpc_request_duration_seconds_bucket[5m]))
```

### Active Connections
```promql
grpc_active_connections
```

## Deployment

### Local Development
```bash
python server.py  # Start gRPC + metrics server
python client.py  # Test the service
curl http://localhost:8000/metrics  # View metrics
```

### Docker
```bash
docker-compose up  # Includes Prometheus + Grafana
```

### Production
- Use proper service discovery for Prometheus
- Set up alerting rules
- Monitor resource usage
- Use TLS for production gRPC endpoints
