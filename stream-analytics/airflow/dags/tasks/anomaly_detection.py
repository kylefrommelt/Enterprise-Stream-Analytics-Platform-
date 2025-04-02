"""
Anomaly Detection Implementation

This module implements anomaly detection for the streaming analytics pipeline.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
import numpy as np
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

def calculate_zscore(value: float, mean: float, std: float) -> float:
    """Calculate the z-score of a value."""
    return (value - mean) / std if std != 0 else 0

def detect_metric_anomaly(
    hook: PostgresHook,
    metric_name: str,
    query: str,
    threshold: float = 2.0
) -> Dict[str, Any]:
    """Detect anomalies in a metric using z-score analysis."""
    # Get historical data
    results = hook.get_records(query)
    if not results:
        return None
    
    values = [row[0] for row in results]
    current_value = values[-1]
    historical_values = values[:-1]
    
    if not historical_values:
        return None
    
    mean = np.mean(historical_values)
    std = np.std(historical_values)
    zscore = calculate_zscore(current_value, mean, std)
    
    severity = 'HIGH' if abs(zscore) > 3 else 'MEDIUM' if abs(zscore) > threshold else 'LOW'
    
    return {
        'metric_name': metric_name,
        'timestamp': datetime.now(),
        'value': current_value,
        'expected_value': mean,
        'deviation_percentage': abs(zscore * 100),
        'severity': severity
    }

def check_for_anomalies(**kwargs) -> bool:
    """Check for anomalies in the metrics."""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Get hourly metrics for the last 24 hours
    query = """
    SELECT total_events, revenue, unique_users
    FROM hourly_metrics
    WHERE hour_timestamp >= NOW() - INTERVAL '24 hours'
    ORDER BY hour_timestamp
    """
    
    results = hook.get_records(query)
    if not results:
        return True
    
    # Convert to numpy array for calculations
    metrics = np.array(results)
    
    # Calculate z-scores for each metric
    for i, metric_name in enumerate(['hourly_events', 'hourly_revenue', 'hourly_unique_users']):
        values = metrics[:, i]
        mean = np.mean(values[:-1])  # Use all but last value for mean
        std = np.std(values[:-1])
        current_value = values[-1]
        
        if std != 0:
            zscore = (current_value - mean) / std
            severity = 'HIGH' if abs(zscore) > 3 else 'MEDIUM' if abs(zscore) > 2 else 'LOW'
            
            # Store anomaly result
            hook.run("""
                INSERT INTO anomaly_detection_results (
                    metric_name, timestamp, value, expected_value,
                    deviation_percentage, severity
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, parameters=(
                metric_name,
                datetime.now(),
                current_value,
                mean,
                abs(zscore * 100),
                severity
            ))
    
    return True 