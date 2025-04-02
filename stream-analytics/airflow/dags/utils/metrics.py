"""
Metrics tracking and reporting for the streaming analytics pipeline.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram
from .logging_config import get_logger

logger = get_logger(__name__)

# Define Prometheus metrics
EVENTS_PROCESSED = Counter(
    'stream_analytics_events_processed_total',
    'Total number of events processed',
    ['event_type']
)

PROCESSING_TIME = Histogram(
    'stream_analytics_processing_time_seconds',
    'Time taken to process events',
    ['operation']
)

ERROR_COUNT = Counter(
    'stream_analytics_errors_total',
    'Total number of errors encountered',
    ['error_type']
)

QUEUE_SIZE = Gauge(
    'stream_analytics_queue_size',
    'Current size of the processing queue'
)

class MetricsCollector:
    """Collector for pipeline metrics."""
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.metrics: Dict[str, Any] = {}
    
    def start_operation(self, operation_name: str) -> None:
        """Start timing an operation."""
        self.start_time = datetime.utcnow()
        self.metrics[operation_name] = {
            'start_time': self.start_time,
            'status': 'in_progress'
        }
    
    def end_operation(self, operation_name: str, status: str = 'success') -> None:
        """End timing an operation and record metrics."""
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            PROCESSING_TIME.labels(operation=operation_name).observe(duration)
            
            self.metrics[operation_name].update({
                'end_time': datetime.utcnow(),
                'duration': duration,
                'status': status
            })
    
    def record_event(self, event_type: str) -> None:
        """Record a processed event."""
        EVENTS_PROCESSED.labels(event_type=event_type).inc()
    
    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        ERROR_COUNT.labels(error_type=error_type).inc()
    
    def update_queue_size(self, size: int) -> None:
        """Update the current queue size."""
        QUEUE_SIZE.set(size)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics

# Create a global metrics collector instance
metrics_collector = MetricsCollector() 