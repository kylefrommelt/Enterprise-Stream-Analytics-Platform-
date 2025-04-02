"""
SQLAlchemy models for the streaming analytics pipeline.
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class UserActivity(Base):
    __tablename__ = 'user_activity'

    event_id = Column(String(36), primary_key=True)
    user_id = Column(String(50), nullable=False)
    session_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    event_type = Column(String(20), nullable=False)
    page_url = Column(Text, nullable=False)
    referrer_url = Column(Text)
    device_type = Column(String(20))
    browser = Column(String(20))
    os = Column(String(20))
    screen_resolution = Column(String(20))
    ip_address = Column(String(45))
    country = Column(String(2))
    city = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    product_id = Column(String(50))
    product_category = Column(String(50))
    product_price = Column(Numeric(10, 2))
    quantity = Column(Integer)
    custom_attributes = Column(JSONB)
    created_at = Column(DateTime, server_default='CURRENT_TIMESTAMP')

class HourlyMetrics(Base):
    __tablename__ = 'hourly_metrics'

    id = Column(Integer, primary_key=True)
    hour_timestamp = Column(DateTime, nullable=False, unique=True)
    total_events = Column(Integer, nullable=False)
    unique_users = Column(Integer, nullable=False)
    purchase_count = Column(Integer, nullable=False)
    revenue = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default='CURRENT_TIMESTAMP')

class DashboardMetadata(Base):
    __tablename__ = 'dashboard_metadata'

    id = Column(Integer, primary_key=True)
    last_processed_timestamp = Column(DateTime, nullable=False)
    total_records_processed = Column(BigInteger, nullable=False)
    processing_duration_seconds = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default='CURRENT_TIMESTAMP')

class DataQualityCheck(Base):
    __tablename__ = 'data_quality_checks'

    id = Column(Integer, primary_key=True)
    check_name = Column(String(100), nullable=False)
    check_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    failure_count = Column(Integer, nullable=False)
    total_records = Column(Integer, nullable=False)
    check_timestamp = Column(DateTime, nullable=False)
    details = Column(JSONB)
    created_at = Column(DateTime, server_default='CURRENT_TIMESTAMP')

class AnomalyDetectionResult(Base):
    __tablename__ = 'anomaly_detection_results'

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    expected_value = Column(Numeric(10, 2), nullable=False)
    deviation_percentage = Column(Numeric(5, 2), nullable=False)
    severity = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default='CURRENT_TIMESTAMP') 