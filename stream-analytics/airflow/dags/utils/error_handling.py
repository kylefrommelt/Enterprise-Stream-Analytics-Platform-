"""
Error handling utilities for the streaming analytics pipeline.
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

class DataQualityError(PipelineError):
    """Exception raised when data quality checks fail."""
    def __init__(self, message: str, check_name: str, failure_count: int):
        super().__init__(
            message=message,
            error_code="DATA_QUALITY_ERROR",
            details={
                "check_name": check_name,
                "failure_count": failure_count
            }
        )

class AnomalyDetectionError(PipelineError):
    """Exception raised when anomaly detection fails."""
    def __init__(self, message: str, metric_name: str, severity: str):
        super().__init__(
            message=message,
            error_code="ANOMALY_DETECTION_ERROR",
            details={
                "metric_name": metric_name,
                "severity": severity
            }
        )

class DatabaseError(PipelineError):
    """Exception raised for database-related errors."""
    def __init__(self, message: str, operation: str, table: str):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={
                "operation": operation,
                "table": table
            }
        )

class KafkaError(PipelineError):
    """Exception raised for Kafka-related errors."""
    def __init__(self, message: str, topic: str, operation: str):
        super().__init__(
            message=message,
            error_code="KAFKA_ERROR",
            details={
                "topic": topic,
                "operation": operation
            }
        )

def handle_pipeline_error(error: PipelineError, logger: logging.Logger) -> None:
    """Handle pipeline errors by logging and potentially triggering alerts."""
    error_details = {
        "error_code": error.error_code,
        "message": error.message,
        "timestamp": error.timestamp.isoformat(),
        "details": error.details
    }
    
    logger.error(f"Pipeline error occurred: {error_details}")
    
    # Here you could add additional error handling logic:
    # - Send alerts to monitoring system
    # - Update error tracking system
    # - Trigger recovery procedures 