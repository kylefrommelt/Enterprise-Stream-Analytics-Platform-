"""
Streaming Analytics Pipeline DAG

This DAG orchestrates the streaming analytics pipeline, including:
1. Checking streaming services health
2. Running data quality checks
3. Generating reports
4. Managing Spark jobs
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
from tasks.data_quality import run_data_quality_checks
from tasks.anomaly_detection import check_for_anomalies
from tasks.dashboard import update_dashboard_metadata

# Default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

# Define the DAG
dag = DAG(
    'streaming_analytics_pipeline',
    default_args=default_args,
    description='Orchestrate the streaming analytics pipeline',
    schedule_interval='0 * * * *',  # Run every hour
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['streaming', 'kafka', 'spark', 'analytics'],
)

# Task to initialize database schema
init_db = PostgresOperator(
    task_id='init_database',
    postgres_conn_id='postgres_default',
    sql='/opt/airflow/dags/sql/init.sql',
    dag=dag,
)

# Task to check Kafka health
check_kafka = SimpleHttpOperator(
    task_id='check_kafka_health',
    http_conn_id='kafka_connect_http',
    endpoint='/connectors',
    method='GET',
    response_check=lambda response: len(response.json()) >= 0,
    log_response=True,
    dag=dag,
)

# Task to check Schema Registry health
check_schema_registry = SimpleHttpOperator(
    task_id='check_schema_registry_health',
    http_conn_id='schema_registry_http',
    endpoint='/subjects',
    method='GET',
    response_check=lambda response: len(response.json()) >= 0,
    log_response=True,
    dag=dag,
)

# Task to submit the user activity processor Spark job
submit_user_activity_processor = SparkSubmitOperator(
    task_id='submit_user_activity_processor',
    application='/opt/spark/work-dir/spark/user_activity_processor.py',
    conn_id='spark_default',
    verbose=True,
    executor_cores=2,
    executor_memory='2g',
    num_executors=2,
    name='user_activity_processor',
    application_args=[],
    conf={
        'spark.dynamicAllocation.enabled': 'false',
        'spark.sql.streaming.schemaInference': 'true',
    },
    dag=dag,
)

# Task to execute data quality checks
data_quality_check = PythonOperator(
    task_id='data_quality_check',
    python_callable=run_data_quality_checks,
    provide_context=True,
    dag=dag,
)

# Task to generate hourly metrics report
generate_hourly_report = PostgresOperator(
    task_id='generate_hourly_report',
    postgres_conn_id='postgres_default',
    sql="""
    INSERT INTO hourly_metrics (
        hour_timestamp,
        total_events,
        unique_users,
        purchase_count,
        revenue,
        created_at
    )
    SELECT 
        date_trunc('hour', timestamp) as hour_timestamp,
        COUNT(*) as total_events,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_count,
        SUM(CASE WHEN event_type = 'purchase' THEN quantity * product_price ELSE 0 END) as revenue,
        NOW() as created_at
    FROM user_activity
    WHERE 
        timestamp >= date_trunc('hour', NOW() - INTERVAL '1 hour') AND
        timestamp < date_trunc('hour', NOW())
    GROUP BY 
        date_trunc('hour', timestamp);
    """,
    dag=dag,
)

# Task to check for anomalies in metrics
anomaly_detection = PythonOperator(
    task_id='anomaly_detection',
    python_callable=check_for_anomalies,
    provide_context=True,
    dag=dag,
)

# Task to update dashboard metadata
update_dashboard = PythonOperator(
    task_id='update_dashboard_metadata',
    python_callable=update_dashboard_metadata,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
init_db >> check_kafka >> check_schema_registry >> submit_user_activity_processor
submit_user_activity_processor >> data_quality_check
data_quality_check >> [generate_hourly_report, anomaly_detection]
[generate_hourly_report, anomaly_detection] >> update_dashboard 