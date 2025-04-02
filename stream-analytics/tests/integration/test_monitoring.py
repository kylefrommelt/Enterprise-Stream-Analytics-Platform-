"""
Integration tests for the monitoring system.
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram
from ..utils.logging_config import get_logger
from ..utils.metrics import metrics_collector

logger = get_logger(__name__)

# Test configuration
GRAFANA_URL = "http://grafana:3000"
PROMETHEUS_URL = "http://prometheus:9090"
ALERTMANAGER_URL = "http://alertmanager:9093"

@pytest.fixture(scope="module")
def setup_test_metrics():
    """Setup test metrics and cleanup after tests."""
    # Create test metrics
    test_counter = Counter('test_counter_total', 'Test counter')
    test_gauge = Gauge('test_gauge', 'Test gauge')
    test_histogram = Histogram('test_histogram_seconds', 'Test histogram')
    
    yield test_counter, test_gauge, test_histogram
    
    # Cleanup
    metrics_collector.metrics.clear()

def test_metrics_collection(setup_test_metrics):
    """Test that metrics are being collected correctly."""
    test_counter, test_gauge, test_histogram = setup_test_metrics
    
    # Record some test metrics
    test_counter.inc()
    test_gauge.set(42)
    test_histogram.observe(0.5)
    
    # Wait for Prometheus to scrape
    time.sleep(5)
    
    # Query Prometheus
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", 
                          params={'query': 'test_counter_total'})
    assert response.status_code == 200
    result = response.json()
    assert float(result['data']['result'][0]['value'][1]) == 1.0

def test_grafana_dashboard():
    """Test that Grafana dashboard is accessible and contains expected panels."""
    response = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/stream-analytics")
    assert response.status_code == 200
    dashboard = response.json()
    
    # Check for required panels
    panel_titles = [panel['title'] for panel in dashboard['dashboard']['panels']]
    required_panels = [
        "Events Processed Rate",
        "Error Rate",
        "Average Processing Time",
        "Processing Queue Size"
    ]
    assert all(panel in panel_titles for panel in required_panels)

def test_alert_rules():
    """Test that alert rules are properly configured."""
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/rules")
    assert response.status_code == 200
    rules = response.json()
    
    # Check for required alert rules
    rule_names = [rule['name'] for group in rules['data']['groups'] 
                 for rule in group['rules']]
    required_rules = [
        "HighErrorRate",
        "ProcessingTimeHigh",
        "QueueSizeHigh",
        "NoEventsProcessed"
    ]
    assert all(rule in rule_names for rule in required_rules)

def test_alert_triggering(setup_test_metrics):
    """Test that alerts are triggered when conditions are met."""
    test_counter, test_gauge, test_histogram = setup_test_metrics
    
    # Simulate high error rate
    for _ in range(10):
        metrics_collector.record_error("test_error")
    
    # Wait for alert evaluation
    time.sleep(15)
    
    # Check Alertmanager for active alerts
    response = requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts")
    assert response.status_code == 200
    alerts = response.json()
    
    # Verify alert is present
    assert any(alert['labels']['alertname'] == 'HighErrorRate' 
              for alert in alerts)

def test_metrics_persistence():
    """Test that metrics persist across restarts."""
    # Record some metrics
    metrics_collector.record_event("test_event")
    metrics_collector.update_queue_size(100)
    
    # Simulate service restart
    metrics_collector.metrics.clear()
    
    # Verify metrics are still available in Prometheus
    time.sleep(5)
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", 
                          params={'query': 'stream_analytics_events_processed_total'})
    assert response.status_code == 200
    result = response.json()
    assert float(result['data']['result'][0]['value'][1]) > 0 