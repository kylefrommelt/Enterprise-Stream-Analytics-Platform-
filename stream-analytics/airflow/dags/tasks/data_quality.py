"""
Data Quality Check Implementation

This module implements various data quality checks for the streaming analytics pipeline.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

def run_null_checks(hook: PostgresHook) -> Dict[str, Any]:
    """Check for null values in critical fields."""
    query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(*) FILTER (WHERE user_id IS NULL) as null_user_ids,
        COUNT(*) FILTER (WHERE timestamp IS NULL) as null_timestamps,
        COUNT(*) FILTER (WHERE event_type IS NULL) as null_event_types
    FROM user_activity
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    
    result = hook.get_first(query)
    return {
        'check_name': 'null_check',
        'check_type': 'completeness',
        'status': 'PASS' if result[1] == 0 and result[2] == 0 and result[3] == 0 else 'FAIL',
        'failure_count': result[1] + result[2] + result[3],
        'total_records': result[0],
        'check_timestamp': datetime.now(),
        'details': {
            'null_user_ids': result[1],
            'null_timestamps': result[2],
            'null_event_types': result[3]
        }
    }

def run_value_range_checks(hook: PostgresHook) -> Dict[str, Any]:
    """Check for values within expected ranges."""
    query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(*) FILTER (WHERE product_price < 0) as negative_prices,
        COUNT(*) FILTER (WHERE quantity < 0) as negative_quantities,
        COUNT(*) FILTER (WHERE latitude < -90 OR latitude > 90) as invalid_latitudes,
        COUNT(*) FILTER (WHERE longitude < -180 OR longitude > 180) as invalid_longitudes
    FROM user_activity
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    
    result = hook.get_first(query)
    return {
        'check_name': 'value_range_check',
        'check_type': 'validity',
        'status': 'PASS' if result[1] == 0 and result[2] == 0 and result[3] == 0 and result[4] == 0 else 'FAIL',
        'failure_count': result[1] + result[2] + result[3] + result[4],
        'total_records': result[0],
        'check_timestamp': datetime.now(),
        'details': {
            'negative_prices': result[1],
            'negative_quantities': result[2],
            'invalid_latitudes': result[3],
            'invalid_longitudes': result[4]
        }
    }

def run_uniqueness_checks(hook: PostgresHook) -> Dict[str, Any]:
    """Check for duplicate event IDs."""
    query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(*) - COUNT(DISTINCT event_id) as duplicate_events
    FROM user_activity
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    
    result = hook.get_first(query)
    return {
        'check_name': 'uniqueness_check',
        'check_type': 'uniqueness',
        'status': 'PASS' if result[1] == 0 else 'FAIL',
        'failure_count': result[1],
        'total_records': result[0],
        'check_timestamp': datetime.now(),
        'details': {
            'duplicate_events': result[1]
        }
    }

def run_data_quality_checks(**kwargs) -> bool:
    """Run data quality checks on processed data."""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Run null checks
    null_check_query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(*) FILTER (WHERE user_id IS NULL) as null_user_ids,
        COUNT(*) FILTER (WHERE timestamp IS NULL) as null_timestamps,
        COUNT(*) FILTER (WHERE event_type IS NULL) as null_event_types
    FROM user_activity
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    
    result = hook.get_first(null_check_query)
    
    # Store check results
    hook.run("""
        INSERT INTO data_quality_checks (
            check_name, check_type, status, failure_count,
            total_records, check_timestamp, details
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, parameters=(
        'null_check',
        'completeness',
        'PASS' if result[1] == 0 and result[2] == 0 and result[3] == 0 else 'FAIL',
        result[1] + result[2] + result[3],
        result[0],
        datetime.now(),
        {'null_user_ids': result[1], 'null_timestamps': result[2], 'null_event_types': result[3]}
    ))
    
    return True 