# Production Deployment Guide

This guide provides instructions for deploying the Real-Time Streaming Analytics Pipeline to a production environment.

## Deployment Options

There are two main options for deploying the Stream Analytics Pipeline to production:

1. **Helm Deployment**: Recommended for most production environments
2. **Kustomize Deployment**: For environments with existing Kustomize workflows

## Prerequisites

- Kubernetes cluster (version 1.18+)
- Helm (version 3.2.0+) or Kustomize (included in recent kubectl versions)
- Persistent volume provisioning capability
- Access to container registry for storing custom images
- Domain name and TLS certificates for secure access

## Pre-Deployment Steps

### 1. Build and Push Docker Images

Build and push all required custom images to your container registry:

```bash
# Set your container registry
REGISTRY="your-registry.example.com"

# Build and push data generator image
docker build -t $REGISTRY/streaming-data-generator:latest ./kafka/data-generator/
docker push $REGISTRY/streaming-data-generator:latest

# Build and push spark processor image
docker build -t $REGISTRY/streaming-spark:latest -f ./spark/Dockerfile ./
docker push $REGISTRY/streaming-spark:latest
```

### 2. Prepare Configuration

Ensure all configuration files are properly set up for production:

- `config/sources.yaml` - Adjust data generation rates and retention settings
- `config/data_quality.yaml` - Set appropriate thresholds and alerting
- `config/monitoring.yaml` - Configure monitoring with production endpoints

### 3. Set Up Secrets

Create Kubernetes secrets for sensitive information:

```bash
# Create secret for database credentials
kubectl create secret generic stream-analytics-db-credentials \
  --from-literal=username=airflow \
  --from-literal=password=your-secure-password

# Create secret for MinIO credentials
kubectl create secret generic stream-analytics-minio-credentials \
  --from-literal=root-user=minio \
  --from-literal=root-password=your-secure-minio-password
```

## Deployment with Helm

### 1. Create a Custom Values File

Create a `production-values.yaml` file with your production-specific settings:

```yaml
global:
  environment: production
  domain: stream-analytics.example.com
  storageClass: managed-premium # Adjust based on your cloud provider

images:
  registry: your-registry.example.com
  repository: yourcompany
  tag: latest

kafka:
  replicaCount: 3
  persistence:
    size: 100Gi

spark:
  master:
    replicaCount: 1
  worker:
    replicaCount: 3

postgresql:
  auth:
    existingSecret: stream-analytics-db-credentials
  persistence:
    size: 20Gi

minio:
  auth:
    existingSecret: stream-analytics-minio-credentials
  persistence:
    size: 100Gi

ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls: true
```

### 2. Install with Helm

```bash
# Add required repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install the chart
helm install stream-analytics ./helm/stream-analytics -f production-values.yaml -n stream-analytics --create-namespace
```

### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -n stream-analytics

# Check services
kubectl get svc -n stream-analytics

# Check ingress
kubectl get ingress -n stream-analytics
```

## Deployment with Kustomize

### 1. Create a Production Overlay

If you have specific customizations beyond the provided example in `kubernetes/examples/overlays/production`, create your own:

```bash
cp -r kubernetes/examples/overlays/production kubernetes/overlays/my-production
```

Edit the `kubernetes/overlays/my-production/kustomization.yaml` file to match your requirements.

### 2. Deploy with Kustomize

```bash
# Apply the production configuration
kubectl apply -k kubernetes/overlays/my-production -n stream-analytics --create-namespace
```

### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -n stream-analytics

# Check all resources
kubectl get all -n stream-analytics
```

## Post-Deployment Steps

### 1. Set Up Monitoring

1. Access Grafana at `https://grafana.your-domain.com`
2. Import the default dashboards
3. Set up alerting rules

### 2. Schedule Regular Backups

Set up backups for critical components:

```bash
# Example backup command for PostgreSQL
kubectl exec -n stream-analytics deployment/stream-analytics-postgresql -- pg_dump -U airflow > backup.sql
```

### 3. Set Up Regular Health Checks

Implement health checks to monitor the deployment:

```bash
# Example health check command
curl -s https://airflow.your-domain.com/health | grep "healthy"
```

## Scaling the Deployment

### Horizontal Scaling

To scale components horizontally:

```bash
# Scale up data generator
kubectl scale deployment stream-analytics-data-generator --replicas=5 -n stream-analytics

# Scale up Spark workers
kubectl scale deployment stream-analytics-spark-worker --replicas=5 -n stream-analytics
```

### Vertical Scaling

To adjust resource allocations, update your Helm values or Kustomize overlays and reapply the configuration.

## Updating the Deployment

### Helm Updates

```bash
# Update dependencies
helm repo update

# Upgrade the deployment
helm upgrade stream-analytics ./helm/stream-analytics -f production-values.yaml -n stream-analytics
```

### Kustomize Updates

```bash
# Update the overlay and apply
kubectl apply -k kubernetes/overlays/my-production -n stream-analytics
```

## Rollback Procedures

### Helm Rollback

```bash
# List revisions
helm history stream-analytics -n stream-analytics

# Rollback to a specific revision
helm rollback stream-analytics [REVISION] -n stream-analytics
```

### Kustomize Rollback

For Kustomize-based deployments, keep previous versions of your overlay configuration in version control and apply the previous version.

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check pod events, logs, and resource constraints
2. **Connection issues**: Verify network policies and service configuration
3. **Performance problems**: Check resource usage and scaling requirements

### Logs

View logs for specific components:

```bash
# Data generator logs
kubectl logs -n stream-analytics deployment/stream-analytics-data-generator

# Spark processor logs
kubectl logs -n stream-analytics deployment/stream-analytics-spark-processor
```

## Security Considerations

1. Always use TLS for all ingress endpoints
2. Implement network policies to restrict pod communication
3. Regularly rotate credentials and secrets
4. Follow the principle of least privilege for service accounts
5. Keep all components updated with security patches 