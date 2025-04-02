"""
Setup tests for monitoring infrastructure.
"""

import pytest
import requests
import time
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Test configuration
GRAFANA_URL = "http://grafana:3000"
PROMETHEUS_URL = "http://prometheus:9090"
ALERTMANAGER_URL = "http://alertmanager:9093"

def test_grafana_availability():
    """Test that Grafana is running and accessible."""
    response = requests.get(f"{GRAFANA_URL}/api/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_prometheus_availability():
    """Test that Prometheus is running and accessible."""
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/status/config")
    assert response.status_code == 200

def test_alertmanager_availability():
    """Test that Alertmanager is running and accessible."""
    response = requests.get(f"{ALERTMANAGER_URL}/api/v2/status")
    assert response.status_code == 200

def test_prometheus_targets():
    """Test that all required Prometheus targets are up."""
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets")
    assert response.status_code == 200
    targets = response.json()
    
    # Check for required targets
    target_names = [target['labels']['job'] for target in targets['data']['activeTargets']]
    required_targets = [
        'stream_analytics',
        'prometheus',
        'node-exporter',
        'kafka',
        'spark',
        'airflow',
        'postgresql'
    ]
    
    assert all(target in target_names for target in required_targets)

def test_grafana_datasources():
    """Test that Grafana datasources are properly configured."""
    response = requests.get(f"{GRAFANA_URL}/api/datasources")
    assert response.status_code == 200
    datasources = response.json()
    
    # Check for Prometheus datasource
    assert any(ds['type'] == 'prometheus' for ds in datasources)

def test_alertmanager_config():
    """Test that Alertmanager is properly configured."""
    response = requests.get(f"{ALERTMANAGER_URL}/api/v2/status/config")
    assert response.status_code == 200
    config = response.json()
    
    # Check for required configuration
    assert 'route' in config
    assert 'receivers' in config
    assert 'inhibit_rules' in config

def test_metrics_endpoint():
    """Test that the metrics endpoint is accessible and returning data."""
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", 
                          params={'query': 'up'})
    assert response.status_code == 200
    result = response.json()
    assert len(result['data']['result']) > 0 