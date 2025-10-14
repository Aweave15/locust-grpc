#!/bin/bash

# Deploy gRPC service with Locust load testing to Kubernetes

set -e

echo "🚀 Deploying gRPC Service with Load Testing to Kubernetes"
echo "=================================================="

# Build Docker images
echo "📦 Building Docker images..."
docker build -t grpc-prometheus-service:latest .
docker build -f Dockerfile.locust -t locust-grpc:latest .

# Deploy gRPC service
echo "🔧 Deploying gRPC service..."
kubectl apply -f k8s/grpc-service.yaml

# Wait for service to be ready
echo "⏳ Waiting for gRPC service to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/grpc-service

# Deploy Locust master
echo "🎯 Deploying Locust master..."
kubectl apply -f k8s/locust-master.yaml

# Deploy Locust workers
echo "👥 Deploying Locust workers..."
kubectl apply -f k8s/locust-worker.yaml

# Deploy HPA
echo "📈 Deploying Horizontal Pod Autoscalers..."
kubectl apply -f k8s/hpa.yaml

# Wait for Locust to be ready
echo "⏳ Waiting for Locust to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/locust-master

# Get service URLs
echo "🌐 Getting service URLs..."
LOCUST_IP=$(kubectl get service locust-master -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$LOCUST_IP" ]; then
    echo "⚠️  LoadBalancer IP not available. Use port-forward:"
    echo "kubectl port-forward service/locust-master 8089:8089"
    echo "Then access: http://localhost:8089"
else
    echo "✅ Locust Web UI: http://$LOCUST_IP:8089"
fi

# Show status
echo "📊 Deployment Status:"
echo "===================="
kubectl get pods -l app=grpc-service
kubectl get pods -l app=locust-master
kubectl get pods -l app=locust-worker

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Access Locust Web UI to start load testing"
echo "2. Monitor metrics at: kubectl port-forward service/grpc-service 8000:8000"
echo "3. Scale workers: kubectl scale deployment locust-worker --replicas=10"
echo "4. Monitor HPA: kubectl get hpa"
