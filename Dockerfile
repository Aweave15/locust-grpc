FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Generate gRPC code
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. service.proto

# Expose ports
EXPOSE 50051 8000

# Run the server
CMD ["python", "server.py"]
