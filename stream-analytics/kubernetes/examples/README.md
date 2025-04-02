# Kubernetes Examples for Stream Analytics Pipeline

This directory contains example Kubernetes manifests for deploying the Stream Analytics Pipeline using Kustomize.

## Directory Structure

- `data-generator.yaml` - Kubernetes Deployment for the data generator
- `spark-processor.yaml` - Kubernetes Deployment for the Spark processor
- `kustomization.yaml` - Base Kustomize configuration file
- `overlays/` - Environment-specific configurations
  - `development/` - Development environment configurations
  - `production/` - Production environment configurations

## Prerequisites

- Kubernetes cluster (version 1.18+)
- kubectl command-line tool
- Kustomize installed (included in recent kubectl versions)

## Deployment Instructions

### Development Environment

To deploy to a development environment:

```bash
kubectl apply -k overlays/development/
```

This will apply all resources with development-specific patches:
- Lower resource requirements
- Single replicas
- Development-specific configuration

### Production Environment

To deploy to a production environment:

```bash
kubectl apply -k overlays/production/
```

This will apply all resources with production-specific patches:
- Higher resource requirements
- Multiple replicas for high availability
- Production-specific configuration

## Customization

To create your own customizations:

1. Create a new overlay directory for your environment:
   ```bash
   mkdir -p overlays/my-environment/
   ```

2. Create a `kustomization.yaml` file in your overlay directory:
   ```yaml
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   
   resources:
     - ../../
   
   commonLabels:
     environment: my-environment
   
   # Add your patches here
   ```

3. Apply your customized deployment:
   ```bash
   kubectl apply -k overlays/my-environment/
   ```

## Comparing Configurations

To see what the final configurations will look like for each environment, you can run:

```bash
# View development configuration
kubectl kustomize overlays/development/

# View production configuration
kubectl kustomize overlays/production/
```

## Adding New Resources

If you need to add new resources:

1. Create the YAML file for your resource
2. Add it to the `resources` list in the base `kustomization.yaml` file

## Monitoring and Troubleshooting

After deployment, you can monitor your resources:

```bash
# Get all resources in the stream-analytics namespace
kubectl get all -n stream-analytics

# Check deployment status
kubectl get deployments -n stream-analytics

# Check pods
kubectl get pods -n stream-analytics

# View logs
kubectl logs -n stream-analytics deployment/stream-analytics-data-generator
``` 