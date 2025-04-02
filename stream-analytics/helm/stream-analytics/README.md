# Stream Analytics Helm Chart

This Helm chart deploys the Real-Time Streaming Analytics Pipeline on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure
- LoadBalancer support or Ingress controller

## Installing the Chart

Add the repository (if hosted):

```bash
helm repo add stream-analytics https://example.com/charts
helm repo update
```

To install the chart with the release name `my-release`:

```bash
helm install my-release stream-analytics/stream-analytics
```

For local installation from the chart directory:

```bash
helm install my-release ./stream-analytics
```

## Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

```bash
helm delete my-release
```

## Parameters

### Global parameters

| Name                   | Description                                              | Value                         |
|------------------------|----------------------------------------------------------|-------------------------------|
| `global.environment`   | Environment name (production, staging, development)      | `production`                  |
| `global.imagePullSecrets` | Global Docker registry secret names                   | `[]`                          |
| `global.storageClass`  | Global StorageClass for Persistent Volume(s)             | `standard`                    |
| `global.domain`        | Domain for ingress resources                             | `stream-analytics.example.com`|

### Component enablement

| Name              | Description                                   | Value    |
|-------------------|-----------------------------------------------|----------|
| `kafka.enabled`   | Enable Kafka deployment                       | `true`   |
| `spark.enabled`   | Enable Spark deployment                       | `true`   |
| `postgresql.enabled` | Enable PostgreSQL deployment               | `true`   |
| `minio.enabled`   | Enable MinIO deployment                       | `true`   |
| `grafana.enabled` | Enable Grafana deployment                     | `true`   |
| `airflow.enabled` | Enable Airflow deployment                     | `true`   |

### Image parameters

| Name                      | Description                                           | Value                |
|---------------------------|-------------------------------------------------------|----------------------|
| `images.registry`         | Container image registry                              | `docker.io`          |
| `images.repository`       | Container image repository                            | `yourcompany`        |
| `images.pullPolicy`       | Container image pull policy                           | `IfNotPresent`       |
| `images.tag`              | Overrides the image tag                               | `latest`             |

### Data Generator parameters

| Name                               | Description                                          | Value                         |
|------------------------------------|------------------------------------------------------|-------------------------------|
| `dataGenerator.replicaCount`       | Number of Data Generator replicas                    | `1`                           |
| `dataGenerator.image.repository`   | Data Generator image repository                      | `streaming-data-generator`    |
| `dataGenerator.image.tag`          | Data Generator image tag                             | `nil` (defaults to chart version) |
| `dataGenerator.resources`          | Data Generator resource requirements                 | Check `values.yaml`           |
| `dataGenerator.env`                | Environment variables for Data Generator             | Check `values.yaml`           |
| `dataGenerator.configMap.enabled`  | Create a ConfigMap for Data Generator configuration  | `true`                        |
| `dataGenerator.configMap.name`     | Name of the ConfigMap for Data Generator             | `data-generator-config`       |

### Spark Processor parameters

| Name                               | Description                                          | Value                         |
|------------------------------------|------------------------------------------------------|-------------------------------|
| `sparkProcessor.replicaCount`      | Number of Spark Processor replicas                   | `1`                           |
| `sparkProcessor.image.repository`  | Spark Processor image repository                     | `streaming-spark`             |
| `sparkProcessor.image.tag`         | Spark Processor image tag                            | `nil` (defaults to chart version) |
| `sparkProcessor.resources`         | Spark Processor resource requirements                | Check `values.yaml`           |
| `sparkProcessor.env`               | Environment variables for Spark Processor            | Check `values.yaml`           |
| `sparkProcessor.configMap.enabled` | Create a ConfigMap for Spark Processor configuration | `true`                        |
| `sparkProcessor.configMap.name`    | Name of the ConfigMap for Spark Processor            | `spark-config`                |

### Ingress parameters

| Name                       | Description                                           | Value           |
|----------------------------|-------------------------------------------------------|-----------------|
| `ingress.enabled`          | Enable ingress resource                               | `true`          |
| `ingress.className`        | Ingress class name                                    | `nginx`         |
| `ingress.annotations`      | Additional annotations for the Ingress resource       | `{}`            |
| `ingress.hosts`            | Array of hosts and paths to host                      | Check `values.yaml` |
| `ingress.tls`              | Enable TLS configuration                              | `false`         |

## Configuration and Installation Notes

### External Dependencies

The chart has dependencies on the following Helm charts:
- Kafka (Bitnami)
- Spark (Bitnami)
- PostgreSQL (Bitnami)
- MinIO (Bitnami)
- Grafana

### Production Configuration

For production environments, it is recommended to:

1. Set resource limits and requests for all components
2. Enable persistence for all stateful components (Kafka, PostgreSQL, MinIO)
3. Configure secure authentication for all services
4. Set up proper monitoring and alerting

### Scaling

To scale the components:

```bash
kubectl scale --replicas=3 deployment/my-release-data-generator
```

Or update the values in `values.yaml` and upgrade the release:

```bash
helm upgrade my-release ./stream-analytics -f values.yaml
```

## Upgrading

### To 1.0.0

This is the first major release of the chart. 