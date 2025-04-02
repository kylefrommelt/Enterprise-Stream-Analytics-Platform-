"""
Integration Tests for Streaming Analytics Pipeline

This module contains integration tests for the entire streaming analytics pipeline,
including data generation, processing, quality checks, and anomaly detection.
"""

import os
import json
import time
import pytest
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
from confluent_kafka import Producer, Consumer
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests

# Add the airflow dags directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../airflow/dags'))

# Import tasks and utils from the airflow/dags directory
from airflow.dags.tasks.data_quality import run_data_quality_checks
from airflow.dags.tasks.anomaly_detection import check_for_anomalies
from airflow.dags.tasks.dashboard import update_dashboard_metadata
from airflow.dags.utils.logging_config import get_logger
from airflow.dags.utils.metrics import metrics_collector

logger = get_logger(__name__)

# Test configuration
TEST_CONFIG = {
    'kafka': {
        'bootstrap_servers': 'localhost:9092',
        'topic': 'test_user_activity'
    },
    'postgres': {
        'conn_id': 'postgres_default'
    },
    'test_data': {
        'num_records': 100,
        'time_window': timedelta(hours=1)
    }
}

GRAFANA_URL = "http://grafana:3000"
PROMETHEUS_URL = "http://prometheus:9090"
ALERTMANAGER_URL = "http://alertmanager:9093"

@pytest.fixture(scope='module')
def kafka_producer():
    """Create a Kafka producer for test data."""
    producer = Producer({
        'bootstrap.servers': TEST_CONFIG['kafka']['bootstrap_servers'],
        'client.id': 'test_producer'
    })
    yield producer
    producer.flush()
    producer.close()

@pytest.fixture(scope='module')
def kafka_consumer():
    """Create a Kafka consumer for test data."""
    consumer = Consumer({
        'bootstrap.servers': TEST_CONFIG['kafka']['bootstrap_servers'],
        'group.id': 'test_consumer',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([TEST_CONFIG['kafka']['topic']])
    yield consumer
    consumer.close()

@pytest.fixture(scope='module')
def postgres_hook():
    """Create a PostgreSQL hook for database operations."""
    return PostgresHook(postgres_conn_id=TEST_CONFIG['postgres']['conn_id'])

def generate_test_data(num_records: int) -> List[Dict[str, Any]]:
    """Generate test user activity data."""
    data = []
    base_time = datetime.now()
    
    for i in range(num_records):
        event = {
            'event_id': f'test_event_{i}',
            'user_id': f'user_{i % 10}',
            'session_id': f'session_{i % 5}',
            'timestamp': (base_time + timedelta(minutes=i)).isoformat(),
            'event_type': 'view' if i % 3 == 0 else 'purchase' if i % 3 == 1 else 'click',
            'page_url': f'https://example.com/page_{i}',
            'referrer_url': f'https://example.com/referrer_{i}',
            'device_type': 'desktop' if i % 2 == 0 else 'mobile',
            'browser': 'Chrome',
            'os': 'Windows',
            'screen_resolution': '1920x1080',
            'ip_address': f'192.168.1.{i}',
            'country': 'US',
            'city': 'New York',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'product_id': f'product_{i % 5}',
            'product_category': 'Electronics',
            'product_price': 100.0 + i,
            'quantity': 1,
            'custom_attributes': {'test_attr': f'value_{i}'}
        }
        data.append(event)
    
    return data

def test_data_generation_and_ingestion(kafka_producer, postgres_hook):
    """Test data generation and ingestion into Kafka."""
    # Generate test data
    test_data = generate_test_data(TEST_CONFIG['test_data']['num_records'])
    
    # Send data to Kafka
    for event in test_data:
        kafka_producer.produce(
            TEST_CONFIG['kafka']['topic'],
            key=event['event_id'],
            value=json.dumps(event)
        )
    kafka_producer.flush()
    
    # Verify data in PostgreSQL
    query = """
    SELECT COUNT(*) as count
    FROM user_activity
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    result = postgres_hook.get_first(query)
    assert result[0] >= len(test_data)

def test_data_quality_checks(postgres_hook):
    """Test data quality checks."""
    # Run data quality checks
    result = run_data_quality_checks()
    
    # Verify check results
    query = """
    SELECT status, failure_count
    FROM data_quality_checks
    WHERE check_timestamp >= NOW() - INTERVAL '1 hour'
    """
    results = postgres_hook.get_records(query)
    
    # All checks should pass
    assert all(row[0] == 'PASS' for row in results)
    assert all(row[1] == 0 for row in results)

def test_anomaly_detection(postgres_hook):
    """Test anomaly detection."""
    # Run anomaly detection
    result = check_for_anomalies()
    
    # Verify anomaly results
    query = """
    SELECT severity, deviation_percentage
    FROM anomaly_detection_results
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    results = postgres_hook.get_records(query)
    
    # No high severity anomalies should be detected
    assert not any(row[0] == 'HIGH' for row in results)

def test_hourly_metrics_generation(postgres_hook):
    """Test hourly metrics generation."""
    # Verify hourly metrics
    query = """
    SELECT 
        total_events,
        unique_users,
        purchase_count,
        revenue
    FROM hourly_metrics
    WHERE hour_timestamp >= NOW() - INTERVAL '1 hour'
    """
    result = postgres_hook.get_first(query)
    
    # Verify metrics are reasonable
    assert result[0] > 0  # Total events
    assert result[1] > 0  # Unique users
    assert result[2] >= 0  # Purchase count
    assert result[3] >= 0  # Revenue

def test_dashboard_metadata(postgres_hook):
    """Test dashboard metadata updates."""
    # Run dashboard metadata update
    result = update_dashboard_metadata()
    
    # Verify metadata
    query = """
    SELECT 
        total_records_processed,
        processing_duration_seconds,
        status
    FROM dashboard_metadata
    WHERE last_processed_timestamp >= NOW() - INTERVAL '1 hour'
    ORDER BY created_at DESC
    LIMIT 1
    """
    result = postgres_hook.get_first(query)
    
    # Verify metadata values
    assert result[0] > 0  # Records processed
    assert result[1] >= 0  # Processing duration
    assert result[2] == 'SUCCESS'  # Status 