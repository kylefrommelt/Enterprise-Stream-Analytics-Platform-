"""
Dashboard Metadata Update Implementation

This module implements the dashboard metadata update functionality.
"""

from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook

def update_dashboard_metadata(**kwargs) -> bool:
    """Update dashboard metadata with the latest processing information."""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Get the latest processing information
    query = """
    SELECT 
        MAX(timestamp) as last_processed_timestamp,
        COUNT(*) as total_records_processed,
        EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp))) as processing_duration_seconds
    FROM user_activity
    WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    
    result = hook.get_first(query)
    if not result or not result[0]:
        return False
    
    # Update dashboard metadata
    hook.run("""
        INSERT INTO dashboard_metadata (
            last_processed_timestamp,
            total_records_processed,
            processing_duration_seconds,
            status,
            error_message
        ) VALUES (%s, %s, %s, %s, %s)
    """, parameters=(
        result[0],
        result[1],
        int(result[2]),
        'SUCCESS',
        None
    ))
    
    return True 