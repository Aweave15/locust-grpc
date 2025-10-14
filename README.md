# Async gRPC Service with Prometheus Metrics

This project demonstrates how to build an async Python gRPC service with Prometheus metrics collection and exposure.

## Features

- Async gRPC service implementation
- Prometheus metrics collection (request count, duration, errors)
- Metrics exposure endpoint
- Example client for testing
- Docker support

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate gRPC code:
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. service.proto
```

3. Run the server:
```bash
python server.py
```

4. Run the client (in another terminal):
```bash
python client.py
```

5. View metrics:
```bash
curl http://localhost:8000/metrics
```

## Docker

```bash
docker build -t grpc-prometheus-service .
docker run -p 50051:50051 -p 8000:8000 grpc-prometheus-service
```
