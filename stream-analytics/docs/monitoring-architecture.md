# Stream Analytics Monitoring Architecture

This document provides an overview of the monitoring architecture implemented in the Stream Analytics project. The architecture is designed to provide comprehensive observability into the health, performance, and data quality of the streaming pipeline.

## Architecture Overview

The monitoring architecture consists of the following components:

1. **Prometheus** - Time series database for storing metrics
2. **Alertmanager** - Alert handling and routing
3. **Grafana** - Visualization and dashboarding
4. **Prometheus Adapter** - Custom metrics API for Kubernetes HPA
5. **Exporters** - Various components that export metrics from services
6. **Custom Instrumentation** - Application-level metrics

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌───────────┐    ┌────────────┐     ┌──────────────────┐   │
│  │           │    │            │     │                  │   │
│  │  Grafana  │◄───┤ Prometheus ├────►│  Alertmanager    │   │
│  │           │    │            │     │                  │   │
│  └───────────┘    └──────┬─────┘     └──────────────────┘   │
│                          │                     │            │
│                          │                     │            │
│                          ▼                     ▼            │
│  ┌───────────────────────────────────────┐    ┌─────────┐   │
│  │                                       │    │         │   │
│  │  Service Metrics                      │    │ Slack/  │   │
│  │  - Kafka, Spark, Airflow, etc.        │    │ Email/  │   │
│  │  - Data Generator                     │    │ PagerDuty│   │
│  │  - Data Quality Metrics               │    │         │   │
│  │                                       │    └─────────┘   │
│  └───────────────────────────────────────┘                  │
│                                                             │
│  ┌────────────────────┐                                     │
│  │                    │                                     │
│  │ Prometheus Adapter │ ────► Kubernetes HPA                │
│  │                    │                                     │
│  └────────────────────┘                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Metrics Collection

### Infrastructure Metrics

- **Kafka Metrics**: Broker health, topic throughput, consumer lag
- **Spark Metrics**: Executor usage, job completion, processing lag
- **Airflow Metrics**: DAG success/failure, task duration
- **Database Metrics**: PostgreSQL and MinIO usage and health

### Application Metrics

- **Data Generator**: Records generated per second, batch sizes
- **Spark Processor**: Processing time, records processed per second

### Data Quality Metrics

- **Null Rates**: Percentage of null values in key fields
- **Schema Violations**: Count of records with schema validation failures
- **Duplicates**: Rate of duplicate records
- **Range Violations**: Fields with values outside expected ranges
- **Anomaly Scores**: Statistical anomalies in data streams

## Alerting Configuration

Alerts are configured in Prometheus and routed through Alertmanager:

1. **Severity Levels**:
   - Critical: Requires immediate attention, impacts service availability
   - Warning: Potential issues that don't affect availability but need attention
   - Info: Informational alerts

2. **Alert Routing**:
   - Critical alerts: Slack #critical-channel, PagerDuty (optional)
   - Warning alerts: Slack #warning-channel, Email (optional)

3. **Alert Categories**:
   - Service alerts: Component failures, high resource usage
   - Data quality alerts: Data integrity issues
   - Pipeline alerts: Processing delays, data flow issues

## Dashboards

The monitoring solution includes pre-configured Grafana dashboards:

1. **Kafka Dashboard**: Monitors Kafka performance including message rates, consumer lag, and cluster health.
2. **Data Quality Dashboard**: Visualizes data quality metrics including null rates, schema violations, and anomaly scores.
3. **Pipeline Overview**: High-level summary of the entire pipeline's health and throughput.
4. **Component-specific Dashboards**: Detailed metrics for each main component.

## Auto-scaling with Custom Metrics

The Prometheus Adapter exposes metrics for Kubernetes Horizontal Pod Autoscaler (HPA):

1. **Resource-based Scaling**: CPU and memory utilization
2. **Custom Metrics Scaling**:
   - Consumer group lag (for Spark processors)
   - Message rate (for data generators)
   - Processing time (for stream processors)

## Implementing Custom Metrics

To add custom metrics to your application components:

1. **Python Applications**:
   ```python
   from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server

   # Create metrics
   NULL_RATE = Gauge('stream_analytics_null_rate', 'Null rate by field', ['source', 'field'])
   RECORDS_PROCESSED = Counter('stream_analytics_records_processed', 'Records processed', ['source'])
   PROCESSING_TIME = Histogram('stream_analytics_processing_time_seconds', 'Time spent processing batch', ['source'])
   
   # Start metrics server on port 8000
   start_http_server(8000)
   
   # Update metrics
   NULL_RATE.labels(source='transactions', field='customer_id').set(0.02)
   RECORDS_PROCESSED.labels(source='transactions').inc(100)
   ```

2. **Spark Applications**:
   ```scala
   import org.apache.spark.metrics.source.Source
   import com.codahale.metrics.{Gauge, MetricRegistry}
   
   class DataQualityMetrics extends Source {
     override val sourceName = "DataQuality"
     override val metricRegistry = new MetricRegistry()
     
     // Register metrics
     metricRegistry.register(MetricRegistry.name("nullRate", "customerId"), 
       new Gauge[Double] { override def getValue: Double = calculateNullRate("customer_id") })
   }
   ```

## Configuring the Monitoring Stack

The monitoring stack is deployed as part of the Helm chart with the following configuration options:

```yaml
monitoring:
  enabled: true
  prometheus:
    persistence:
      enabled: true
      size: 10Gi
  alertmanager:
    enabled: true
    slack:
      enabled: true
      webhook_url: "https://hooks.slack.com/services/..."
      channel: "#alerts"
  grafana:
    enabled: true
    adminPassword: "admin"
  prometheusAdapter:
    enabled: true
```

## Best Practices

1. **Cardinality Management**: Limit high-cardinality label combinations to avoid Prometheus performance issues
2. **Alerting Hygiene**: Configure proper alerting thresholds to avoid alert fatigue
3. **Dashboard Organization**: Structure dashboards hierarchically (overview → detail)
4. **Metric Naming**: Use consistent naming conventions (e.g., `stream_analytics_metric_name`)
5. **Retention Policies**: Configure appropriate data retention based on storage capacity

## Troubleshooting

Common issues and solutions:

1. **Missing metrics**: Check that exporters are running and endpoints are accessible
2. **Alert storms**: Review and adjust alert thresholds
3. **Grafana visualization issues**: Verify Prometheus data source configuration
4. **HPA not scaling on custom metrics**: Check Prometheus Adapter configuration and metrics availability 