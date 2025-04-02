# Getting Started with the Real-Time Streaming Analytics Pipeline

This guide will help you set up and run the Real-Time Streaming Analytics Pipeline project locally.

## Prerequisites

Ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/) (version 20.10 or newer)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or newer)
- [Python](https://www.python.org/downloads/) (version 3.8 or newer)
- [Git](https://git-scm.com/downloads) (version 2.30 or newer)

## Clone the Repository

```bash
git clone https://github.com/yourusername/stream-analytics.git
cd stream-analytics
```

## Environment Setup

1. Create a Python virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required Python packages:

```bash
pip install -r requirements.txt
```

## Starting the Infrastructure

1. Start all services using Docker Compose:

```bash
docker-compose up -d
```

This will start the following services:
- Zookeeper
- Kafka
- Schema Registry
- Kafka Connect
- Spark Master and Worker
- PostgreSQL
- Airflow Webserver
- MinIO (S3-compatible storage)
- Grafana
- Data Generator

2. Check if all services are running:

```bash
docker-compose ps
```

## Accessing the Services

Once the services are running, you can access them through your browser:

- Spark UI: [http://localhost:8080](http://localhost:8080)
- Airflow UI: [http://localhost:8090](http://localhost:8090)
- MinIO Console: [http://localhost:9001](http://localhost:9001) (Username: minio, Password: minio123)
- Grafana: [http://localhost:3000](http://localhost:3000) (Username: admin, Password: admin)
- Schema Registry UI: [http://localhost:8081](http://localhost:8081)
- Kafka Connect UI: [http://localhost:8083](http://localhost:8083)

## Project Structure Overview

- `/kafka`: Kafka producers, consumers, and configuration files
- `/spark`: Spark streaming jobs for data processing
- `/airflow`: Airflow DAGs for workflow orchestration
- `/utils`: Utility functions for monitoring and data quality
- `/config`: Configuration files for the pipeline
- `/data`: Sample data and schemas
- `/tests`: Unit and integration tests

## Running the Pipeline

1. The data generator will automatically start producing data to Kafka once the infrastructure is up.

2. Monitor Kafka topics to see incoming data:

```bash
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list
```

3. Check topic details:

```bash
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --describe --topic user-activity
```

4. Access the Airflow UI to trigger DAGs:

- Open [http://localhost:8090](http://localhost:8090)
- Login with default credentials (Username: airflow, Password: airflow)
- Enable and trigger the `streaming_analytics_pipeline` DAG

5. View processed data in Grafana:

- Open [http://localhost:3000](http://localhost:3000)
- Login with default credentials (Username: admin, Password: admin)
- Navigate to the Streaming Analytics dashboards

## Running Tests

To run the test suite:

```bash
pytest tests/
```

To check code quality:

```bash
flake8
black --check .
```

## Customizing the Pipeline

### Modifying Data Sources

Edit the `config/sources.yaml` file to:
- Change data generation rates
- Add new data sources
- Modify existing data source configurations

### Adding Data Quality Checks

Edit the `config/data_quality.yaml` file to:
- Add new data quality checks
- Modify thresholds for existing checks
- Configure alerting settings

### Creating New Spark Jobs

1. Create a new Python script in the `spark` directory
2. Add the job to the Airflow DAG in `airflow/dags/streaming_pipeline_dag.py`

## Troubleshooting

### Common Issues

1. **Services not starting properly**:
   - Check Docker logs: `docker-compose logs <service-name>`
   - Ensure all ports are available on your machine

2. **No data flowing through the pipeline**:
   - Check Kafka topics: `docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic user-activity --from-beginning`
   - Verify the data generator is running: `docker-compose logs data-generator`

3. **Spark jobs failing**:
   - Check Spark UI for error logs
   - Verify Spark configurations in `docker-compose.yml`

### Resetting the Environment

To stop and remove all containers, networks, and volumes:

```bash
docker-compose down -v
```

To restart from a clean state:

```bash
docker-compose down -v
docker-compose up -d
```

## Contributing

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Next Steps

After getting familiar with the basic setup, you can:

1. Explore the data quality monitoring system
2. Add your own custom data sources
3. Create new analytical dashboards in Grafana
4. Extend the Spark processing with custom business logic
5. Implement advanced alerting based on data patterns 