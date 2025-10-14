"""
Locust configuration file for gRPC load testing.
"""
from locust_grpc_test import WebsiteUser, LoadTestUser

# User classes to run
user_classes = [WebsiteUser, LoadTestUser]

# Default configuration
host = "localhost:50051"  # Override with --host in Kubernetes
