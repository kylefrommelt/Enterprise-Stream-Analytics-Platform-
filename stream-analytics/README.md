# Real-Time Streaming Analytics Pipeline

A production-grade data engineering project demonstrating real-time streaming analytics using Apache Kafka, Apache Spark, and Delta Lake.

## Project Overview

This project implements a complete real-time data processing pipeline that:

1. Ingests streaming data from multiple sources using Kafka
2. Processes data in real-time with Spark Streaming 
3. Stores processed data in a Delta Lake for both batch and streaming access
4. Orchestrates workflows with Apache Airflow
5. Provides real-time dashboards and alerts
6. Includes data quality monitoring and validation
7. Demonstrates CI/CD pipelines for data engineering

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Data       │    │  Kafka      │    │  Spark      │    │  Delta      │
│  Sources    │───▶│  Cluster    │───▶│  Streaming  │───▶│  Lake       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                            │                  │
                                            │                  │
                                      ┌─────▼─────┐      ┌─────▼─────┐
                                      │  Data     │      │  BI &     │
                                      │  Quality  │      │  Analytics│
                                      └─────┬─────┘      └───────────┘
                                            │
                                            │
                                      ┌─────▼─────┐
                                      │  Alerts & │
                                      │  Monitoring│
                                      └───────────┘
```

## Project Structure

- `/kafka` - Kafka producers, consumers, and configuration
- `/spark` - Spark streaming jobs and batch processing
- `/airflow` - Airflow DAGs and operators for orchestration
- `/utils` - Utility functions and shared code
- `/tests` - Unit and integration tests
- `/docs` - Project documentation
- `/data` - Sample data and schemas
- `/config` - Configuration files
- `/helm` - Kubernetes Helm charts for deployment

## Getting Started

See the detailed [Getting Started Guide](GETTING_STARTED.md) for complete setup instructions.

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Java 11+
- Maven

### Installation

#### Local Development

1. Clone the repository
2. Run `docker-compose up -d` to start the infrastructure
3. Configure the data sources in `config/sources.yaml`
4. Start the Airflow server with `python -m airflow standalone`

#### Kubernetes Deployment

For production deployments, use our Helm chart:

```bash
# Add dependencies first
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install the chart
helm install stream-analytics ./helm/stream-analytics
```

For detailed deployment instructions, see [Helm Deployment Guide](helm/README.md).

## Features

- Real-time data ingestion from various sources
- Stream processing with exactly-once semantics
- Data quality validation and monitoring
- Automated alerting for anomalies
- Integration with BI tools
- Scalable architecture
- Production-ready Kubernetes deployment

## Technologies Used

- Apache Kafka
- Apache Spark Streaming
- Delta Lake
- Apache Airflow
- Docker
- Kubernetes
- Helm
- Python
- SQL
- Great Expectations
- Grafana/Superset

## Documentation

For more information about the project, consult the following documents:

- [Project Overview](PROJECT.md) - Detailed information about the project architecture
- [Getting Started Guide](GETTING_STARTED.md) - Step-by-step guide to set up and run the project
- [Helm Deployment Guide](helm/README.md) - Instructions for Kubernetes deployments

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests. 