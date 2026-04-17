# Deployment Guide - PDF Accessibility Compliance Engine

## Overview

Comprehensive deployment guide for production deployment of the PDF Accessibility Compliance Engine with all enhanced features.

**Target Environments:** Docker, Kubernetes, Cloud (AWS/GCP/Azure)  
**Deployment Strategy:** Blue-Green, Rolling Updates  
**Monitoring:** Prometheus, Grafana, CloudWatch

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration Management](#configuration-management)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Scaling Strategy](#scaling-strategy)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+ SSD
- Network: 1 Gbps

### Software Requirements

```bash
# Required
- Python 3.11+
- Docker 24.0+
- Docker Compose 2.20+

# Optional (for Kubernetes)
- kubectl 1.28+
- Helm 3.12+

# Optional (for monitoring)
- Prometheus 2.45+
- Grafana 10.0+
```

### API Keys & Credentials

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

---

## Environment Configuration

### 1. Create Environment File

Create `.env` file in project root:

```bash
# Application Settings
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production

# API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
API_RATE_LIMIT=100
API_TIMEOUT=30

# Server Configuration
HOST=0.0.0.0
PORT=5000
WORKERS=4

# Memory Configuration
MAX_MEMORY_MB=100
MAX_FILE_SIZE_MB=50

# PII Detection
PII_SENSITIVITY=medium
PII_CACHE_SIZE=1000

# AI Validation
AI_VALIDATION_ENABLED=true
AI_CONFIDENCE_THRESHOLD=60.0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/pdf-compliance/app.log

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Optional: Redis for caching
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600

# Optional: Database
DATABASE_ENABLED=false
DATABASE_URL=postgresql://user:pass@localhost:5432/pdf_compliance

# Security
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SSL_ENABLED=true
```

### 2. Validate Configuration

```bash
# Check environment variables
python -c "from src.config import Config; print(Config.validate())"

# Test API connectivity
python test_gemini_api.sh
```

---

## Docker Deployment

### 1. Build Docker Image

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "src.app:app"]
```

**Build and Run:**

```bash
# Build image
docker build -t pdf-compliance:latest .

# Run container
docker run -d \
    --name pdf-compliance \
    -p 5000:5000 \
    --env-file .env \
    --memory="2g" \
    --cpus="2" \
    --restart=unless-stopped \
    pdf-compliance:latest

# Check logs
docker logs -f pdf-compliance

# Check health
curl http://localhost:5000/health
```

### 2. Docker Compose Deployment

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  app:
    build: .
    image: pdf-compliance:latest
    container_name: pdf-compliance-app
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - redis
    volumes:
      - ./logs:/var/log/pdf-compliance
    networks:
      - pdf-compliance-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: pdf-compliance-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - pdf-compliance-network
    restart: unless-stopped
    command: redis-server --appendonly yes

  prometheus:
    image: prom/prometheus:latest
    container_name: pdf-compliance-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - pdf-compliance-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: pdf-compliance-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - pdf-compliance-network
    restart: unless-stopped

networks:
  pdf-compliance-network:
    driver: bridge

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
```

**Deploy with Docker Compose:**

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Scale application
docker-compose up -d --scale app=3

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Kubernetes Deployment

### 1. Create Kubernetes Manifests

**namespace.yaml:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pdf-compliance
```

**configmap.yaml:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdf-compliance-config
  namespace: pdf-compliance
data:
  FLASK_ENV: "production"
  LOG_LEVEL: "INFO"
  PII_SENSITIVITY: "medium"
  AI_VALIDATION_ENABLED: "true"
```

**secret.yaml:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: pdf-compliance-secrets
  namespace: pdf-compliance
type: Opaque
stringData:
  GEMINI_API_KEY: "your-api-key-here"
  SECRET_KEY: "your-secret-key-here"
```

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-compliance
  namespace: pdf-compliance
  labels:
    app: pdf-compliance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdf-compliance
  template:
    metadata:
      labels:
        app: pdf-compliance
    spec:
      containers:
      - name: pdf-compliance
        image: pdf-compliance:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
          name: http
        envFrom:
        - configMapRef:
            name: pdf-compliance-config
        - secretRef:
            name: pdf-compliance-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

**service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: pdf-compliance-service
  namespace: pdf-compliance
spec:
  type: LoadBalancer
  selector:
    app: pdf-compliance
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
```

**ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pdf-compliance-ingress
  namespace: pdf-compliance
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: pdf-compliance-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pdf-compliance-service
            port:
              number: 80
```

**hpa.yaml (Horizontal Pod Autoscaler):**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pdf-compliance-hpa
  namespace: pdf-compliance
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pdf-compliance
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets (use kubectl create secret instead for production)
kubectl create secret generic pdf-compliance-secrets \
  --from-literal=GEMINI_API_KEY=your-key \
  --from-literal=SECRET_KEY=your-secret \
  -n pdf-compliance

# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Check deployment status
kubectl get all -n pdf-compliance

# Check logs
kubectl logs -f deployment/pdf-compliance -n pdf-compliance

# Scale deployment
kubectl scale deployment pdf-compliance --replicas=5 -n pdf-compliance

# Rolling update
kubectl set image deployment/pdf-compliance \
  pdf-compliance=pdf-compliance:v2.0.0 \
  -n pdf-compliance

# Rollback
kubectl rollout undo deployment/pdf-compliance -n pdf-compliance
```

---

## Cloud Deployment

### AWS Deployment (ECS/Fargate)

**task-definition.json:**

```json
{
  "family": "pdf-compliance",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "pdf-compliance",
      "image": "your-ecr-repo/pdf-compliance:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "GEMINI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:gemini-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pdf-compliance",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**Deploy to AWS:**

```bash
# Create ECR repository
aws ecr create-repository --repository-name pdf-compliance

# Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker build -t pdf-compliance .
docker tag pdf-compliance:latest your-account.dkr.ecr.us-east-1.amazonaws.com/pdf-compliance:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/pdf-compliance:latest

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster pdf-compliance-cluster \
  --service-name pdf-compliance-service \
  --task-definition pdf-compliance \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### GCP Deployment (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/your-project/pdf-compliance

# Deploy to Cloud Run
gcloud run deploy pdf-compliance \
  --image gcr.io/your-project/pdf-compliance \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars FLASK_ENV=production \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest
```

### Azure Deployment (Container Instances)

```bash
# Create resource group
az group create --name pdf-compliance-rg --location eastus

# Create container registry
az acr create --resource-group pdf-compliance-rg --name pdfcomplianceacr --sku Basic

# Build and push image
az acr build --registry pdfcomplianceacr --image pdf-compliance:latest .

# Deploy container
az container create \
  --resource-group pdf-compliance-rg \
  --name pdf-compliance \
  --image pdfcomplianceacr.azurecr.io/pdf-compliance:latest \
  --cpu 2 \
  --memory 2 \
  --registry-login-server pdfcomplianceacr.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label pdf-compliance \
  --ports 5000 \
  --environment-variables FLASK_ENV=production \
  --secure-environment-variables GEMINI_API_KEY=<your-key>
```

---

## Configuration Management

### Environment-Specific Configurations

**Development (`config/dev.env`):**
```bash
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
PII_SENSITIVITY=low
AI_VALIDATION_ENABLED=false
```

**Staging (`config/staging.env`):**
```bash
FLASK_ENV=staging
FLASK_DEBUG=False
LOG_LEVEL=INFO
PII_SENSITIVITY=medium
AI_VALIDATION_ENABLED=true
```

**Production (`config/prod.env`):**
```bash
FLASK_ENV=production
FLASK_DEBUG=False
LOG_LEVEL=WARNING
PII_SENSITIVITY=high
AI_VALIDATION_ENABLED=true
```

### Configuration Validation

```python
# src/config.py
import os
from typing import Dict, Any

class Config:
    @staticmethod
    def validate() -> Dict[str, Any]:
        """Validate all required configuration"""
        required = [
            'GEMINI_API_KEY',
            'SECRET_KEY',
            'FLASK_ENV'
        ]
        
        missing = [key for key in required if not os.getenv(key)]
        
        if missing:
            raise ValueError(f"Missing required config: {missing}")
        
        return {
            'status': 'valid',
            'environment': os.getenv('FLASK_ENV'),
            'features': {
                'pii_detection': True,
                'ai_validation': os.getenv('AI_VALIDATION_ENABLED', 'true') == 'true',
                'redis_cache': os.getenv('REDIS_ENABLED', 'false') == 'true'
            }
        }
```

---

## Security Hardening

### 1. SSL/TLS Configuration

**nginx.conf:**

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://pdf-compliance:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. API Key Management

```bash
# Use secrets management
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name pdf-compliance/gemini-api-key \
  --secret-string "your-api-key"

# GCP Secret Manager
echo -n "your-api-key" | gcloud secrets create gemini-api-key --data-file=-

# Azure Key Vault
az keyvault secret set \
  --vault-name pdf-compliance-vault \
  --name gemini-api-key \
  --value "your-api-key"
```

### 3. Network Security

```yaml
# NetworkPolicy for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pdf-compliance-netpol
  namespace: pdf-compliance
spec:
  podSelector:
    matchLabels:
      app: pdf-compliance
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 6379  # Redis
```

---

## Monitoring & Logging

### Prometheus Configuration

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'pdf-compliance'
    static_configs:
      - targets: ['app:5000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import dashboard JSON for:
- Request rate and latency
- Error rates
- Memory and CPU usage
- PII detection metrics
- AI validation scores

### Logging Configuration

```python
# src/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/var/log/pdf-compliance/app.log'),
        logging.StreamHandler()
    ]
)
```

---

## Backup & Recovery

### Data Backup Strategy

```bash
# Backup Redis data
docker exec pdf-compliance-redis redis-cli BGSAVE
docker cp pdf-compliance-redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz /var/log/pdf-compliance/

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env config/
```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective):** 1 hour
2. **RPO (Recovery Point Objective):** 15 minutes
3. **Backup Frequency:** Daily
4. **Backup Retention:** 30 days

---

## Scaling Strategy

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up -d --scale app=5

# Kubernetes
kubectl scale deployment pdf-compliance --replicas=10 -n pdf-compliance

# Auto-scaling based on metrics
kubectl autoscale deployment pdf-compliance \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n pdf-compliance
```

### Vertical Scaling

```yaml
# Increase resources in deployment
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

---

## Troubleshooting

### Common Issues

**1. High Memory Usage**
```bash
# Check memory usage
docker stats pdf-compliance

# Solution: Increase memory limit or optimize caching
```

**2. Slow Response Times**
```bash
# Check logs for bottlenecks
docker logs pdf-compliance | grep "slow"

# Solution: Enable Redis caching, increase workers
```

**3. API Rate Limiting**
```bash
# Check rate limit headers
curl -I https://api.yourdomain.com/api/v2/analyze

# Solution: Adjust rate limits in configuration
```

---

*Deployment Guide Version: 1.0.0*  
*Last Updated: April 17, 2026*