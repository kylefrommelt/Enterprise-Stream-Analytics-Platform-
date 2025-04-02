# Stream Analytics API Documentation

## Overview
This document provides detailed information about the APIs available in the Stream Analytics Pipeline.

## Metrics API

### Prometheus Metrics Endpoint
```
GET /metrics
```
Exposes Prometheus metrics for the streaming analytics pipeline.

#### Available Metrics

1. **Event Processing**
   ```
   stream_analytics_events_processed_total{event_type="<type>"}
   ```
   - Counter metric tracking total events processed
   - Labels: event_type

2. **Processing Time**
   ```
   stream_analytics_processing_time_seconds{operation="<name>"}
   ```
   - Histogram metric for processing duration
   - Labels: operation

3. **Error Tracking**
   ```
   stream_analytics_errors_total{error_type="<type>"}
   ```
   - Counter metric for error occurrences
   - Labels: error_type

4. **Queue Size**
   ```
   stream_analytics_queue_size
   ```
   - Gauge metric for current queue size

## Data Quality API

### Quality Check Results
```
GET /api/v1/quality-checks
```
Returns the latest data quality check results.

#### Response
```json
{
  "checks": [
    {
      "check_name": "string",
      "check_type": "string",
      "status": "string",
      "failure_count": 0,
      "total_records": 0,
      "check_timestamp": "datetime",
      "details": {}
    }
  ]
}
```

## Anomaly Detection API

### Anomaly Results
```
GET /api/v1/anomalies
```
Returns detected anomalies.

#### Response
```json
{
  "anomalies": [
    {
      "metric_name": "string",
      "timestamp": "datetime",
      "value": 0.0,
      "expected_value": 0.0,
      "deviation_percentage": 0.0,
      "severity": "string"
    }
  ]
}
```

## Dashboard API

### Dashboard Metadata
```
GET /api/v1/dashboard/metadata
```
Returns current dashboard metadata.

#### Response
```json
{
  "last_processed_timestamp": "datetime",
  "total_records_processed": 0,
  "processing_duration_seconds": 0,
  "status": "string",
  "error_message": "string"
}
```

## Monitoring API

### Health Check
```
GET /health
```
Returns the health status of the service.

#### Response
```json
{
  "status": "ok|error",
  "components": {
    "kafka": "ok|error",
    "spark": "ok|error",
    "postgresql": "ok|error"
  }
}
```

### Metrics Collection
```
GET /metrics/collection
```
Returns detailed metrics collection status.

#### Response
```json
{
  "status": "ok|error",
  "last_collection": "datetime",
  "collection_interval": 0,
  "metrics_count": 0
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### Common Error Codes
- `E001`: Service unavailable
- `E002`: Invalid request
- `E003`: Database error
- `E004`: Processing error
- `E005`: Configuration error

## Rate Limiting

- Default rate limit: 100 requests per minute
- Rate limit headers:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 99
  X-RateLimit-Reset: 1234567890
  ```

## Authentication

All API endpoints require authentication using API keys:
```
Authorization: Bearer <api_key>
``` 