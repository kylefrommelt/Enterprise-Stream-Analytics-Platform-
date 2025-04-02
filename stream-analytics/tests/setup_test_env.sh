#!/bin/bash

# Exit on error
set -e

echo "Setting up test environment for Stream Analytics Pipeline..."

# Create test directories
mkdir -p test_data
mkdir -p test_logs

# Create test Kafka topic
echo "Creating test Kafka topic..."
docker-compose exec kafka kafka-topics --create \
    --topic test_user_activity \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 3

# Initialize test database
echo "Initializing test database..."
docker-compose exec postgres psql -U postgres -d stream_analytics -f /opt/airflow/dags/sql/init.sql

# Install test dependencies
echo "Installing test dependencies..."
pip install -r requirements-test.txt

# Create test configuration
echo "Creating test configuration..."
cat > test_config.json << EOL
{
    "kafka": {
        "bootstrap_servers": "localhost:9092",
        "topic": "test_user_activity"
    },
    "postgres": {
        "conn_id": "postgres_default"
    },
    "test_data": {
        "num_records": 100,
        "time_window": "1h"
    }
}
EOL

echo "Test environment setup complete!"
echo "To run tests: pytest tests/integration/test_pipeline.py -v" 