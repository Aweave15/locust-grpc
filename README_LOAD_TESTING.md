# gRPC Load Testing with Locust in Kubernetes

This project demonstrates how to effectively load balance and test a gRPC service using Locust in a distributed Kubernetes environment.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Locust Master │    │  gRPC Service    │    │   Prometheus    │
│   (Web UI)      │◄──►│  (3 replicas)    │◄──►│   (Metrics)     │
│   Port: 8089    │    │  Port: 50051     │    │   Port: 8000    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
    ┌────▼────┐              ┌───▼───┐
    │ Workers │              │  HPA  │
    │(5-20)   │              │(3-10) │
    └─────────┘              └───────┘
```

## 🚀 Quick Start

### 1. Deploy Everything
```bash
./deploy.sh
```

### 2. Access Locust Web UI
```bash
# If LoadBalancer is available
kubectl get service locust-master

# Otherwise, use port-forward
kubectl port-forward service/locust-master 8089:8089
# Then visit: http://localhost:8089
```

### 3. Start Load Testing
1. Open Locust Web UI
2. Set users: 100, spawn rate: 10
3. Click "Start swarming"
4. Monitor real-time results

### 4. Monitor Metrics
```bash
# View Prometheus metrics
kubectl port-forward service/grpc-service 8000:8000
curl http://localhost:8000/metrics
```

## 📊 Load Testing Features

### **Multiple Test Scenarios**
- **Unary calls**: Simple request-response (weight: 3)
- **Server streaming**: Stream responses (weight: 1)  
- **Client streaming**: Stream requests (weight: 1)
- **High-frequency calls**: Burst testing (weight: 10)

### **Realistic User Behavior**
```python
class WebsiteUser(GRPCLocustUser):
    wait_time = lambda self: random.uniform(0.1, 0.5)  # Normal users
    weight = 1

class LoadTestUser(GRPCLoadTestUser):
    wait_time = lambda self: random.uniform(0.01, 0.1)  # Heavy users
    weight = 2
```

### **Auto-scaling**
- **gRPC Service**: 3-10 replicas based on CPU/memory
- **Locust Workers**: 2-20 replicas based on CPU usage
- **Dynamic scaling**: Responds to load automatically

## 🔧 Configuration

### **Load Balancer**
```python
# Round-robin with health checking
lb = HealthCheckLoadBalancer([
    "grpc-service-1:50051",
    "grpc-service-2:50051", 
    "grpc-service-3:50051"
])
```

### **Kubernetes Resources**
```yaml
# gRPC Service
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# Locust Workers  
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## 📈 Monitoring & Metrics

### **Prometheus Metrics**
- `grpc_requests_total{method, status}` - Request count
- `grpc_request_duration_seconds{method}` - Response time
- `grpc_errors_total{method, error_type}` - Error count
- `grpc_active_connections` - Active connections

### **Locust Metrics**
- Real-time RPS (Requests Per Second)
- Response time percentiles (50th, 95th, 99th)
- Error rates and types
- User count and distribution

### **Kubernetes Metrics**
- Pod resource usage (CPU, memory)
- HPA scaling events
- Service endpoint health

## 🎯 Why Locust for gRPC?

### **✅ Advantages**
1. **Native Python**: Same language as your gRPC service
2. **Async Support**: Perfect for async gRPC calls
3. **Distributed Mode**: Built-in master-worker architecture
4. **Kubernetes Native**: Container-friendly design
5. **Real-time UI**: Live monitoring and control
6. **Flexible Scenarios**: Multiple user types and behaviors

### **❌ Why NOT Others**
- **K6**: JavaScript-only, complex distributed setup
- **Artillery**: Poor gRPC support, not async-native
- **JMeter**: Java-based, heavy resource usage
- **Custom Scripts**: No distributed coordination, manual work

## 🔍 Testing Scenarios

### **1. Baseline Load Test**
- Users: 50
- Duration: 10 minutes
- Goal: Establish baseline performance

### **2. Stress Test**
- Users: 200
- Duration: 5 minutes
- Goal: Find breaking point

### **3. Spike Test**
- Users: 50 → 500 → 50
- Duration: 15 minutes
- Goal: Test auto-scaling

### **4. Endurance Test**
- Users: 100
- Duration: 1 hour
- Goal: Test stability over time

## 🛠️ Troubleshooting

### **Common Issues**

1. **Workers not connecting to master**
   ```bash
   kubectl logs deployment/locust-worker
   # Check master host/port configuration
   ```

2. **High error rates**
   ```bash
   kubectl get pods -l app=grpc-service
   # Check if gRPC service is healthy
   ```

3. **Resource limits hit**
   ```bash
   kubectl describe pod <pod-name>
   # Check resource usage and limits
   ```

### **Scaling Commands**
```bash
# Scale gRPC service
kubectl scale deployment grpc-service --replicas=5

# Scale Locust workers
kubectl scale deployment locust-worker --replicas=10

# Check HPA status
kubectl get hpa
```

## 📚 Files Overview

- `load_balancer.py` - gRPC load balancer with health checking
- `locust_grpc_test.py` - Locust user classes for gRPC testing
- `locustfile.py` - Locust configuration
- `k8s/` - Kubernetes manifests for deployment
- `alternative_tools.py` - Comparison with other tools
- `LOAD_TESTING_ANALYSIS.md` - Detailed analysis of tool choices

## 🎉 Results

This setup provides:
- **Production-ready load testing** for gRPC services
- **Distributed testing** across multiple Kubernetes nodes
- **Real-time monitoring** with Prometheus integration
- **Auto-scaling** based on load and resource usage
- **Comprehensive metrics** for performance analysis

Perfect for testing gRPC services at scale in Kubernetes! 🚀
