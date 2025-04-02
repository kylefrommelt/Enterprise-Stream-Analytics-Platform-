#!/usr/bin/env python3
"""
Data Generator for Streaming Analytics Pipeline

This script generates synthetic data for the streaming analytics pipeline
based on the configuration in the sources.yaml file.
"""

import os
import time
import json
import uuid
import random
import logging
import datetime
import threading
from typing import Dict, List, Any, Optional

import yaml
import schedule
import numpy as np
from faker import Faker
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Faker for generating realistic data
fake = Faker()

# Load configuration
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/app/config/sources.yaml')
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
SCHEMA_REGISTRY_URL = os.environ.get('SCHEMA_REGISTRY_URL', 'http://schema-registry:8081')


def load_config() -> Dict[str, Any]:
    """Load and return the configuration from the YAML file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {CONFIG_PATH}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def load_schema(schema_file: str) -> Dict[str, Any]:
    """Load and return the Avro schema from the specified file."""
    try:
        # Get the absolute path of the schema file
        if not os.path.isabs(schema_file):
            schema_file = os.path.join('/app', schema_file)
        
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        logger.info(f"Loaded schema from {schema_file}")
        return schema
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        raise


def create_kafka_producer() -> Producer:
    """Create and return a Kafka producer instance."""
    try:
        producer_config = {
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'data-generator',
            'acks': 'all',
            'retries': 5,
            'retry.backoff.ms': 500,
        }
        producer = Producer(producer_config)
        logger.info(f"Created Kafka producer with bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
        return producer
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        raise


def create_schema_registry_client() -> SchemaRegistryClient:
    """Create and return a Schema Registry client."""
    try:
        schema_registry_config = {
            'url': SCHEMA_REGISTRY_URL
        }
        client = SchemaRegistryClient(schema_registry_config)
        logger.info(f"Created Schema Registry client with URL: {SCHEMA_REGISTRY_URL}")
        return client
    except Exception as e:
        logger.error(f"Failed to create Schema Registry client: {e}")
        raise


class DataGenerator:
    """Class responsible for generating and sending synthetic data to Kafka."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the data generator with the given configuration."""
        self.config = config
        self.producer = create_kafka_producer()
        self.schema_registry = create_schema_registry_client()
        self.serializers = {}
        self.active_threads = []
        self.running = True
        
    def initialize_serializers(self) -> None:
        """Initialize Avro serializers for each data source."""
        for source_name, source_config in self.config['sources'].items():
            try:
                schema_file = source_config['schema_file']
                schema = load_schema(schema_file)
                serializer = AvroSerializer(schema, self.schema_registry, {'auto.register.schemas': True})
                self.serializers[source_name] = serializer
                logger.info(f"Initialized serializer for source: {source_name}")
            except Exception as e:
                logger.error(f"Failed to initialize serializer for source {source_name}: {e}")
                raise
    
    def generate_user_activity_data(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic user activity data based on the source configuration."""
        gen_config = source_config['generation']
        actions = gen_config['actions']
        
        event_id = str(uuid.uuid4())
        user_id = f"user_{random.randint(1, gen_config['users'])}"
        session_id = f"session_{random.randint(1, gen_config['sessions'])}"
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        event_type = random.choice(actions)
        
        device_types = ["desktop", "mobile", "tablet", "other"]
        browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]
        os_list = ["Windows", "MacOS", "Linux", "iOS", "Android"]
        
        # Generate a product ID and related data only for relevant event types
        product_related = event_type in ["view", "purchase", "add_to_cart", "remove_from_cart"]
        product_id = f"product_{random.randint(1, 1000)}" if product_related else None
        product_category = random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]) if product_related else None
        product_price = round(random.uniform(10.0, 500.0), 2) if product_related else None
        quantity = random.randint(1, 5) if product_related and event_type != "view" else None
        
        return {
            "event_id": event_id,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "page_url": f"https://example.com/{fake.uri_path()}",
            "referrer_url": f"https://example.com/{fake.uri_path()}" if random.random() > 0.3 else None,
            "device_info": {
                "device_type": random.choice(device_types),
                "browser": random.choice(browsers),
                "os": random.choice(os_list),
                "screen_resolution": f"{random.choice([1024, 1366, 1920])}x{random.choice([768, 900, 1080])}"
            },
            "geo_data": {
                "ip_address": fake.ipv4(),
                "country": fake.country_code(),
                "city": fake.city(),
                "latitude": float(fake.latitude()),
                "longitude": float(fake.longitude())
            },
            "product_id": product_id,
            "product_category": product_category,
            "product_price": product_price,
            "quantity": quantity,
            "custom_attributes": {
                f"attr_{i}": f"value_{random.randint(1, 100)}" 
                for i in range(random.randint(0, 5))
            }
        }
    
    def generate_iot_sensor_data(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic IoT sensor data based on the source configuration."""
        gen_config = source_config['generation']
        metrics = gen_config['metrics']
        locations = gen_config['locations']
        
        sensor_id = f"sensor_{random.randint(1, gen_config['sensors'])}"
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        location = random.choice(locations)
        
        # Generate metric readings with some realistic patterns
        readings = {}
        if 'temperature' in metrics:
            # Temperature between 18°C and 30°C with some normal distribution
            readings['temperature'] = round(random.normalvariate(24, 3), 1)
        
        if 'humidity' in metrics:
            # Humidity between 30% and 70%
            readings['humidity'] = round(random.normalvariate(50, 10), 1)
        
        if 'pressure' in metrics:
            # Atmospheric pressure around 1013 hPa
            readings['pressure'] = round(random.normalvariate(1013, 5), 1)
        
        if 'battery_level' in metrics:
            # Battery level between 0% and 100%
            readings['battery_level'] = round(random.uniform(20, 100), 1)
        
        return {
            "sensor_id": sensor_id,
            "timestamp": timestamp,
            "location": location,
            "readings": readings,
            "status": "active" if random.random() > 0.05 else "inactive",
            "maintenance_required": random.random() < 0.02
        }
    
    def generate_transaction_data(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic transaction data based on the source configuration."""
        gen_config = source_config['generation']
        payment_methods = gen_config['payment_methods']
        amount_range = gen_config['amount_range']
        
        transaction_id = str(uuid.uuid4())
        user_id = f"user_{random.randint(1, gen_config['users'])}"
        product_id = f"product_{random.randint(1, gen_config['products'])}"
        timestamp = int(datetime.datetime.now().timestamp() * 1000)
        
        # Generate a realistic transaction amount
        amount = round(random.uniform(amount_range['min'], amount_range['max']), 2)
        
        # Add some product data
        product_name = fake.product_name()
        product_category = random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"])
        
        # Add some payment information
        payment_method = random.choice(payment_methods)
        
        return {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "product_id": product_id,
            "product_name": product_name,
            "product_category": product_category,
            "quantity": random.randint(1, 5),
            "amount": amount,
            "payment_method": payment_method,
            "status": "completed" if random.random() > 0.05 else random.choice(["pending", "failed"]),
            "store_id": f"store_{random.randint(1, 50)}",
            "is_online": random.random() > 0.3
        }
    
    def generate_data(self, source_name: str) -> Dict[str, Any]:
        """Generate data for the specified source."""
        source_config = self.config['sources'][source_name]
        
        if source_name == 'user_activity':
            return self.generate_user_activity_data(source_config)
        elif source_name == 'iot_sensors':
            return self.generate_iot_sensor_data(source_config)
        elif source_name == 'transactions':
            return self.generate_transaction_data(source_config)
        else:
            logger.warning(f"Unknown source type: {source_name}")
            return {}
    
    def send_to_kafka(self, source_name: str, data: Dict[str, Any]) -> None:
        """Serialize and send the data to the appropriate Kafka topic."""
        source_config = self.config['sources'][source_name]
        topic = source_config['topic']
        serializer = self.serializers.get(source_name)
        
        if serializer:
            try:
                # Use a string key (e.g., user_id or sensor_id)
                if 'user_id' in data:
                    key = data['user_id']
                elif 'sensor_id' in data:
                    key = data['sensor_id']
                elif 'transaction_id' in data:
                    key = data['transaction_id']
                else:
                    key = str(uuid.uuid4())
                
                # Serialize the key and value
                key_serializer = StringSerializer('utf_8')
                serialized_key = key_serializer(key)
                serialized_value = serializer(data, SerializationContext(topic, MessageField.VALUE))
                
                # Send the message to Kafka
                self.producer.produce(
                    topic=topic,
                    key=serialized_key,
                    value=serialized_value,
                    on_delivery=self.delivery_report
                )
                
                # Flush to ensure the message is sent
                self.producer.poll(0)
            except Exception as e:
                logger.error(f"Error sending message to Kafka: {e}")
        else:
            logger.error(f"No serializer found for source: {source_name}")
    
    def delivery_report(self, err, msg) -> None:
        """Callback for Kafka message delivery reports."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    def generate_and_send(self, source_name: str, rate: int) -> None:
        """Generate and send data for the specified source at the given rate."""
        interval = 1.0 / rate if rate > 0 else 1.0
        
        logger.info(f"Starting data generation for source: {source_name} at rate: {rate} events/sec")
        
        while self.running:
            start_time = time.time()
            
            # Generate and send the data
            data = self.generate_data(source_name)
            self.send_to_kafka(source_name, data)
            
            # Calculate sleep time to maintain the desired rate
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def start_all_generators(self) -> None:
        """Start data generation for all configured sources in separate threads."""
        for source_name, source_config in self.config['sources'].items():
            # Get the generation rate from the configuration
            rate = source_config['generation']['rate']
            
            # Start a thread for this source
            thread = threading.Thread(
                target=self.generate_and_send,
                args=(source_name, rate),
                daemon=True
            )
            thread.start()
            self.active_threads.append(thread)
            
            logger.info(f"Started generator thread for source: {source_name}")
    
    def stop(self) -> None:
        """Stop all data generation threads."""
        self.running = False
        
        # Wait for all threads to finish
        for thread in self.active_threads:
            thread.join(timeout=5.0)
        
        # Flush and close the Kafka producer
        self.producer.flush()
        logger.info("Stopped all data generators and flushed Kafka producer")


def main():
    """Main entry point for the data generator."""
    try:
        # Load the configuration
        config = load_config()
        
        # Create and initialize the data generator
        generator = DataGenerator(config)
        generator.initialize_serializers()
        
        # Start all generators
        generator.start_all_generators()
        
        # Keep the main thread running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
        if 'generator' in locals():
            generator.stop()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if 'generator' in locals():
            generator.stop()


if __name__ == "__main__":
    main() 