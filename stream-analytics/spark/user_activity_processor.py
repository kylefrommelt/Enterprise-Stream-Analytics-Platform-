#!/usr/bin/env python3
"""
User Activity Data Processor

This Spark Streaming job processes user activity data from Kafka,
performs transformations, and writes the results to Delta Lake.
"""

import os
import sys
import json
import yaml
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, count, sum, avg, explode, 
    expr, when, lit, to_timestamp, hour, minute, second,
    year, month, day, hour
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, TimestampType, MapType,
    ArrayType
)

# Define schema for user activity data
user_activity_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("event_type", StringType(), False),
    StructField("page_url", StringType(), False),
    StructField("referrer_url", StringType(), True),
    StructField("device_info", StructType([
        StructField("device_type", StringType(), False),
        StructField("browser", StringType(), False),
        StructField("os", StringType(), False),
        StructField("screen_resolution", StringType(), True)
    ]), False),
    StructField("geo_data", StructType([
        StructField("ip_address", StringType(), True),
        StructField("country", StringType(), True),
        StructField("city", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True)
    ]), False),
    StructField("product_id", StringType(), True),
    StructField("product_category", StringType(), True),
    StructField("product_price", DoubleType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("custom_attributes", MapType(StringType(), StringType()), False)
])


def load_config():
    """Load configuration from YAML file."""
    config_path = os.environ.get("CONFIG_PATH", "/opt/spark/work-dir/config/sources.yaml")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        print(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def create_spark_session():
    """Create and configure a Spark session."""
    return (
        SparkSession.builder
        .appName("UserActivityProcessor")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints/user_activity")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "minio")
        .config("spark.hadoop.fs.s3a.secret.key", "minio123")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.sql.shuffle.partitions", "10")
        .getOrCreate()
    )


def process_user_activity(spark, config):
    """Process user activity data from Kafka."""
    # Get Kafka topic and other configurations
    kafka_bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    user_activity_topic = config["sources"]["user_activity"]["topic"]
    delta_lake_config = config["sinks"]["delta_lake"]
    
    # Read from Kafka
    df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", user_activity_topic)
        .option("startingOffsets", "latest")
        .load()
    )
    
    # Parse JSON data
    parsed_df = df.select(
        col("key").cast("string"),
        from_json(col("value").cast("string"), user_activity_schema).alias("data"),
        col("timestamp").alias("processing_time")
    ).select("key", "data.*", "processing_time")
    
    # Add timestamp columns for partitioning
    df_with_time = parsed_df.withColumn(
        "event_year", year(col("timestamp"))
    ).withColumn(
        "event_month", month(col("timestamp"))
    ).withColumn(
        "event_day", day(col("timestamp"))
    ).withColumn(
        "event_hour", hour(col("timestamp"))
    )
    
    # ------------ Stream Processing Operations ------------
    
    # 1. Raw events - store all processed events
    raw_events_query = (
        df_with_time.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", delta_lake_config["tables"]["user_activity_hourly"]["checkpoint_location"])
        .partitionBy("event_year", "event_month", "event_day", "event_hour")
        .start(delta_lake_config["tables"]["user_activity_hourly"]["path"])
    )
    
    # 2. Session Analysis - Track user sessions
    session_df = df_with_time.groupBy(
        "session_id", "user_id", 
        window("timestamp", "5 minutes")
    ).agg(
        count("event_id").alias("event_count"),
        count(when(col("event_type") == "view", True)).alias("page_views"),
        count(when(col("event_type") == "click", True)).alias("clicks"),
        count(when(col("event_type") == "purchase", True)).alias("purchases")
    )
    
    # Write session data
    session_query = (
        session_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", "/tmp/checkpoints/user_activity_sessions")
        .start("s3a://data-lake/user_activity/sessions/")
    )
    
    # 3. Product Analysis - Track product interactions
    product_df = df_with_time.filter(
        col("product_id").isNotNull()
    ).groupBy(
        "product_id", "product_category",
        window("timestamp", "1 hour")
    ).agg(
        count("event_id").alias("view_count"),
        count(when(col("event_type") == "add_to_cart", True)).alias("add_to_cart_count"),
        count(when(col("event_type") == "purchase", True)).alias("purchase_count"),
        sum(when(col("event_type") == "purchase", col("quantity") * col("product_price"))).alias("total_revenue")
    )
    
    # Write product data
    product_query = (
        product_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", "/tmp/checkpoints/user_activity_products")
        .start("s3a://data-lake/user_activity/products/")
    )
    
    # 4. User Behavior Analysis
    user_behavior_df = df_with_time.groupBy(
        "user_id", "device_info.device_type",
        window("timestamp", "1 hour")
    ).agg(
        count("event_id").alias("total_events"),
        avg(when(col("event_type") == "purchase", col("product_price"))).alias("avg_purchase_value"),
        count(when(col("event_type") == "purchase", True)).alias("purchase_count")
    )
    
    # Write user behavior data
    user_behavior_query = (
        user_behavior_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", "/tmp/checkpoints/user_activity_behavior")
        .start("s3a://data-lake/user_activity/user_behavior/")
    )
    
    # 5. Geo Analysis
    geo_df = df_with_time.filter(
        col("geo_data.country").isNotNull()
    ).groupBy(
        "geo_data.country", "geo_data.city",
        window("timestamp", "1 hour")
    ).agg(
        count("event_id").alias("total_events"),
        count(when(col("event_type") == "purchase", True)).alias("purchase_count"),
        sum(when(col("event_type") == "purchase", col("quantity") * col("product_price"))).alias("total_revenue")
    )
    
    # Write geo data
    geo_query = (
        geo_df.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", "/tmp/checkpoints/user_activity_geo")
        .start("s3a://data-lake/user_activity/geo/")
    )
    
    # Wait for all queries to terminate
    raw_events_query.awaitTermination()


def main():
    """Main function."""
    try:
        # Load configuration
        config = load_config()
        
        # Create Spark session
        spark = create_spark_session()
        
        # Process user activity data
        process_user_activity(spark, config)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 