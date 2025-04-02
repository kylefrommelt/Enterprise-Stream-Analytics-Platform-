# Helm Charts for Stream Analytics Pipeline

This directory contains Helm charts for deploying the Real-Time Streaming Analytics Pipeline to Kubernetes.

## Available Charts

- `stream-analytics`: The main chart that deploys the complete Real-Time Streaming Analytics Pipeline

## Deployment Options

### Development Environment

For development/testing environments with limited resources:

```bash
helm install stream-analytics ./stream-analytics \
  --set global.environment=development \
  --set kafka.replicaCount=1 \
  --set spark.master.replicaCount=1 \
  --set spark.worker.replicaCount=1 \
  --set monitoring.enabled=false \
  --set ingress.enabled=false
```

### Staging Environment

For staging environments:

```bash
helm install stream-analytics ./stream-analytics \
  --set global.environment=staging \
  --set global.domain=staging.stream-analytics.example.com \
  --set kafka.replicaCount=3 \
  --set spark.master.replicaCount=1 \
  --set spark.worker.replicaCount=2 \
  --set ingress.enabled=true
```

### Production Environment

For production environments:

```bash
helm install stream-analytics ./stream-analytics \
  --set global.environment=production \
  --set global.domain=stream-analytics.example.com \
  --set global.storageClass=managed-premium \
  --set kafka.replicaCount=3 \
  --set spark.master.replicaCount=1 \
  --set spark.worker.replicaCount=3 \
  --set monitoring.enabled=true \
  --set ingress.enabled=true
```

## Customizing Deployments

### Using Values Files

Create a custom values file (e.g., `my-values.yaml`) and override specific values:

```yaml
# my-values.yaml
global:
  environment: production
  domain: stream-analytics.mycompany.com

dataGenerator:
  replicaCount: 2
  resources:
    limits:
      cpu: 1000m
      memory: 1024Mi

kafka:
  replicaCount: 5
  persistence:
    size: 100Gi
```

Then install or upgrade the chart with this values file:

```bash
helm install stream-analytics ./stream-analytics -f my-values.yaml
```

### Cloud Provider Specific Settings

#### AWS

```yaml
global:
  storageClass: gp2

ingress:
  className: alb
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
```

#### Azure

```yaml
global:
  storageClass: managed-premium

ingress:
  className: azure-application-gateway
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
```

#### GCP

```yaml
global:
  storageClass: standard

ingress:
  className: gce
  annotations:
    kubernetes.io/ingress.class: gce
```

## Upgrading

To upgrade an existing deployment:

```bash
helm upgrade stream-analytics ./stream-analytics -f my-values.yaml
```

## Uninstalling

To uninstall a deployment:

```bash
helm uninstall stream-analytics
```

## Troubleshooting

If you encounter issues with Helm deployments, check:

1. Validate the chart for syntax issues:
   ```bash
   helm lint ./stream-analytics
   ```

2. Perform a dry run to see what resources would be created:
   ```bash
   helm install --dry-run --debug stream-analytics ./stream-analytics
   ```

3. Check Kubernetes events:
   ```bash
   kubectl get events --sort-by='.lastTimestamp'
   ```

4. Debug pod issues:
   ```bash
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ``` 