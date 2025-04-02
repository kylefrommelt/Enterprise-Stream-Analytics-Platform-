# Monitoring and Observability Components

This directory contains the configuration for monitoring and observability components of the Stream Analytics Pipeline.

## Directory Structure

```
monitoring/
├── alertmanager/           # Alertmanager configuration
│   ├── config/             # Alertmanager main configuration
│   └── template/           # Alert notification templates
├── grafana/                # Grafana configuration
│   ├── dashboards/         # Dashboard definitions
│   └── provisioning/       # Datasource and dashboard provisioning
├── prometheus/             # Prometheus configuration
│   ├── config/             # Prometheus main configuration
│   └── rules/              # Alerting rules
└── exporters/              # Various metric exporters
    ├── kafka-exporter/     # Kafka metrics exporter
    └── postgres-exporter/  # PostgreSQL metrics exporter
```

## Components Overview

### Prometheus

Prometheus is the central metrics collection system that scrapes and stores time series data. Our configuration includes:

- Scrape configuration for all components (Kafka, Spark, Airflow, custom applications)
- Recording rules for common calculations
- Alert rules for critical conditions

### Alertmanager

Alertmanager handles alerts sent by Prometheus, including:

- Deduplication of similar alerts
- Grouping related alerts
- Routing to appropriate notification channels (Slack, email, PagerDuty)
- Silencing and inhibition mechanisms

### Grafana

Grafana provides visualization dashboards for our metrics, including:

- Kafka monitoring dashboard
- Data quality dashboard 
- Streaming pipeline overview
- System resource utilization

### Metric Exporters

Various exporters that collect and expose metrics from services:

- JMX Exporter for Kafka 
- PostgreSQL Exporter
- Node Exporter for system metrics

## Setup Instructions

### Local Development

For local development with Docker Compose:

1. Start the monitoring stack:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose-monitoring.yml up -d
   ```

2. Access Grafana at http://localhost:3000 (default credentials: admin/admin)
3. Access Prometheus at http://localhost:9090
4. Access Alertmanager at http://localhost:9093

### Kubernetes Deployment

The monitoring stack is deployed as part of the Helm chart:

```bash
helm install stream-analytics ./helm/stream-analytics --set monitoring.enabled=true
```

Configuration options can be customized in the values.yaml file or via --set parameters.

## Custom Metrics Integration

### Adding application metrics

1. For Python applications, use the prometheus_client library:
   ```python
   from prometheus_client import Counter, Gauge, start_http_server
   
   # Expose metrics on port 8000
   start_http_server(8000)
   
   # Define and update metrics
   records_processed = Counter('stream_analytics_records_processed_total', 'Total records processed')
   records_processed.inc(100)
   ```

2. For JVM applications, use the JMX exporter or micrometer.

3. Ensure your application's metrics endpoint is included in the Prometheus scrape configuration:

```yaml
scrape_configs:
  - job_name: 'my-application'
    scrape_interval: 15s
    static_configs:
      - targets: ['my-application:8000']
```

## Available Dashboards

The following dashboards are provided:

- **Kafka Monitoring**: Topic throughput, consumer lag, broker health
- **Data Quality Monitoring**: Null rates, schema violations, anomalies 
- **Pipeline Overview**: End-to-end pipeline health and performance
- **System Monitoring**: CPU, memory, disk usage across components

## Alerting Configuration

Alert rules are defined in Prometheus and processed by Alertmanager. Key alerts include:

- Service availability (component downtime)
- Performance issues (high lag, slow processing)
- Data quality problems (high null rates, schema violations)
- Resource constraints (memory/disk usage)

Edit the alerting rules in `prometheus/rules/` to customize thresholds and conditions.

## Extending the Monitoring Stack

To add new components to monitoring:

1. Configure the component to expose metrics (typically on /metrics endpoint)
2. Add scrape configuration to Prometheus
3. Create or update dashboards in Grafana
4. Define relevant alerting rules

See the [Monitoring Architecture](../docs/monitoring-architecture.md) document for detailed information on the monitoring architecture and best practices. 