-- Create user_activity table
CREATE TABLE IF NOT EXISTS user_activity (
    event_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    page_url TEXT NOT NULL,
    referrer_url TEXT,
    device_type VARCHAR(20),
    browser VARCHAR(20),
    os VARCHAR(20),
    screen_resolution VARCHAR(20),
    ip_address VARCHAR(45),
    country VARCHAR(2),
    city VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    product_id VARCHAR(50),
    product_category VARCHAR(50),
    product_price DECIMAL(10, 2),
    quantity INTEGER,
    custom_attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create hourly_metrics table
CREATE TABLE IF NOT EXISTS hourly_metrics (
    id SERIAL PRIMARY KEY,
    hour_timestamp TIMESTAMP NOT NULL,
    total_events INTEGER NOT NULL,
    unique_users INTEGER NOT NULL,
    purchase_count INTEGER NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hour_timestamp)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_event_type ON user_activity(event_type);
CREATE INDEX IF NOT EXISTS idx_hourly_metrics_timestamp ON hourly_metrics(hour_timestamp);

-- Create dashboard_metadata table
CREATE TABLE IF NOT EXISTS dashboard_metadata (
    id SERIAL PRIMARY KEY,
    last_processed_timestamp TIMESTAMP NOT NULL,
    total_records_processed BIGINT NOT NULL,
    processing_duration_seconds INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create data_quality_checks table
CREATE TABLE IF NOT EXISTS data_quality_checks (
    id SERIAL PRIMARY KEY,
    check_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    failure_count INTEGER NOT NULL,
    total_records INTEGER NOT NULL,
    check_timestamp TIMESTAMP NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create anomaly_detection_results table
CREATE TABLE IF NOT EXISTS anomaly_detection_results (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value DECIMAL(10, 2) NOT NULL,
    expected_value DECIMAL(10, 2) NOT NULL,
    deviation_percentage DECIMAL(5, 2) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 