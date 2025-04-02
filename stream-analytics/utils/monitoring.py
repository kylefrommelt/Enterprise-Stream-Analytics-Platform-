"""
Monitoring and Alerting Utilities

This module provides utilities for monitoring the streaming analytics pipeline
and sending alerts when issues are detected.
"""

import os
import json
import yaml
import time
import logging
import datetime
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertManager:
    """Class to manage alerts for the streaming analytics pipeline."""
    
    def __init__(self, config_path: str):
        """
        Initialize the alert manager with the given configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.alerting_config = self.config.get('alerting', {})
        logger.info(f"Initialized AlertManager with config from {config_path}")
    
    def should_alert(self, data: Dict[str, Any]) -> bool:
        """
        Determine if an alert should be sent based on the data and configuration.
        
        Args:
            data: Data to check against alert thresholds
            
        Returns:
            bool: True if an alert should be sent, False otherwise
        """
        # Get the overall pass rate
        if "summary" in data and "pass_rate" in data["summary"]:
            pass_rate = data["summary"]["pass_rate"]
            
            # Check if the pass rate is below any configured threshold
            email_threshold = self.alerting_config.get('email', {}).get('threshold', 0.0)
            slack_threshold = self.alerting_config.get('slack', {}).get('threshold', 0.0)
            
            return pass_rate < email_threshold or pass_rate < slack_threshold
        
        return False
    
    def send_email_alert(self, data: Dict[str, Any]) -> bool:
        """
        Send an email alert.
        
        Args:
            data: Data to include in the alert
            
        Returns:
            bool: True if the alert was sent successfully, False otherwise
        """
        email_config = self.alerting_config.get('email', {})
        
        if not email_config.get('enabled', False):
            logger.info("Email alerts are disabled")
            return False
        
        # Check if the pass rate is below the threshold
        if "summary" in data and "pass_rate" in data["summary"]:
            pass_rate = data["summary"]["pass_rate"]
            threshold = email_config.get('threshold', 0.0)
            
            if pass_rate >= threshold:
                logger.info(f"Pass rate {pass_rate} is above threshold {threshold}, no email alert needed")
                return False
        
        # Get the recipients
        recipients = email_config.get('recipients', [])
        if not recipients:
            logger.warning("No email recipients configured")
            return False
        
        try:
            # Create the email message
            msg = MIMEMultipart()
            msg['Subject'] = f"Data Quality Alert - Pass Rate: {data['summary']['pass_rate']:.2%}"
            msg['From'] = email_config.get('from', 'alerts@example.com')
            msg['To'] = ', '.join(recipients)
            
            # Create the email body
            body = f"""
            <html>
            <body>
                <h2>Data Quality Alert</h2>
                <p>A data quality alert has been triggered at {datetime.datetime.now()}.</p>
                
                <h3>Summary</h3>
                <ul>
                    <li>Total Checks: {data['summary']['total_checks']}</li>
                    <li>Passed Checks: {data['summary']['passed_checks']}</li>
                    <li>Failed Checks: {data['summary']['failed_checks']}</li>
                    <li>Pass Rate: {data['summary']['pass_rate']:.2%}</li>
                </ul>
                
                <h3>Failed Checks</h3>
                <table border="1">
                    <tr>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Message</th>
                    </tr>
            """
            
            # Add the failed checks to the email body
            for result in data['results']:
                if not result.get('passed', False):
                    body += f"""
                    <tr>
                        <td>{result.get('name', 'N/A')}</td>
                        <td>{result.get('description', 'N/A')}</td>
                        <td>{result.get('message', 'N/A')}</td>
                    </tr>
                    """
            
            body += """
                </table>
                
                <p>Please investigate and resolve these issues.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send the email
            smtp_server = email_config.get('smtp_server', 'localhost')
            smtp_port = email_config.get('smtp_port', 25)
            smtp_user = email_config.get('smtp_user', '')
            smtp_password = email_config.get('smtp_password', '')
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Sent email alert to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    def send_slack_alert(self, data: Dict[str, Any]) -> bool:
        """
        Send a Slack alert.
        
        Args:
            data: Data to include in the alert
            
        Returns:
            bool: True if the alert was sent successfully, False otherwise
        """
        slack_config = self.alerting_config.get('slack', {})
        
        if not slack_config.get('enabled', False):
            logger.info("Slack alerts are disabled")
            return False
        
        # Check if the pass rate is below the threshold
        if "summary" in data and "pass_rate" in data["summary"]:
            pass_rate = data["summary"]["pass_rate"]
            threshold = slack_config.get('threshold', 0.0)
            
            if pass_rate >= threshold:
                logger.info(f"Pass rate {pass_rate} is above threshold {threshold}, no Slack alert needed")
                return False
        
        # Get the webhook URL
        webhook_url = slack_config.get('webhook')
        if not webhook_url:
            logger.warning("No Slack webhook URL configured")
            return False
        
        try:
            # Create the Slack message payload
            timestamp = datetime.datetime.now().isoformat()
            
            # Create blocks for the message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Data Quality Alert - Pass Rate: {data['summary']['pass_rate']:.2%}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Time:* {timestamp}\n*Total Checks:* {data['summary']['total_checks']}\n*Passed:* {data['summary']['passed_checks']}\n*Failed:* {data['summary']['failed_checks']}"
                    }
                },
                {
                    "type": "divider"
                }
            ]
            
            # Add the failed checks to the message
            failed_checks = [result for result in data['results'] if not result.get('passed', False)]
            
            if failed_checks:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Failed Checks:*"
                    }
                })
                
                for result in failed_checks[:5]:  # Limit to 5 failed checks to avoid message size limits
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{result.get('name', 'N/A')}*\n{result.get('description', 'N/A')}\n```{result.get('message', 'N/A')}```"
                        }
                    })
                
                if len(failed_checks) > 5:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"... and {len(failed_checks) - 5} more failed checks."
                        }
                    })
            
            # Send the message to Slack
            payload = {
                "channel": slack_config.get('channel', '#alerts'),
                "username": slack_config.get('username', 'Data Quality Monitor'),
                "icon_emoji": slack_config.get('icon_emoji', ':warning:'),
                "blocks": blocks
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Sent Slack alert to {slack_config.get('channel', '#alerts')}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    def send_alerts(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Send alerts to all configured channels.
        
        Args:
            data: Data to include in the alerts
            
        Returns:
            Dict[str, bool]: Results of sending alerts to each channel
        """
        results = {}
        
        if self.should_alert(data):
            # Send email alert
            results['email'] = self.send_email_alert(data)
            
            # Send Slack alert
            results['slack'] = self.send_slack_alert(data)
        else:
            logger.info("No alerts needed based on current data")
            results['email'] = False
            results['slack'] = False
        
        return results


class ServiceMonitor:
    """Class to monitor the health of services in the streaming analytics pipeline."""
    
    def __init__(self, services: Dict[str, Dict[str, Any]]):
        """
        Initialize the service monitor with the given services.
        
        Args:
            services: Dictionary mapping service names to service configurations
        """
        self.services = services
        logger.info(f"Initialized ServiceMonitor with {len(services)} services")
    
    def check_service(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the health of a service.
        
        Args:
            name: Name of the service
            config: Service configuration
            
        Returns:
            Dict[str, Any]: Service health information
        """
        result = {
            "name": name,
            "status": "unknown",
            "message": "",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            service_type = config.get('type', '')
            
            if service_type == 'http':
                # HTTP health check
                url = config.get('url', '')
                timeout = config.get('timeout', 5)
                headers = config.get('headers', {})
                expected_status = config.get('expected_status', 200)
                
                response = requests.get(url, headers=headers, timeout=timeout)
                
                if response.status_code == expected_status:
                    result['status'] = 'healthy'
                    result['message'] = f"Service is healthy (status code: {response.status_code})"
                else:
                    result['status'] = 'unhealthy'
                    result['message'] = f"Service returned unexpected status code: {response.status_code}"
                
            elif service_type == 'kafka':
                # Kafka health check
                # This would typically involve checking if the Kafka brokers are reachable
                # and if the topics are available
                bootstrap_servers = config.get('bootstrap_servers', '')
                
                # In a real implementation, we would use a Kafka client to check the health
                # For now, we'll just simulate a successful check
                result['status'] = 'healthy'
                result['message'] = f"Kafka service is reachable at {bootstrap_servers}"
                
            elif service_type == 'spark':
                # Spark health check
                # This would typically involve checking if the Spark master is reachable
                # and if the workers are available
                master_url = config.get('master_url', '')
                
                # In a real implementation, we would use a Spark client to check the health
                # For now, we'll just simulate a successful check
                result['status'] = 'healthy'
                result['message'] = f"Spark service is reachable at {master_url}"
                
            else:
                result['status'] = 'unknown'
                result['message'] = f"Unknown service type: {service_type}"
                
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"Error checking service: {str(e)}"
        
        return result
    
    def check_all_services(self) -> Dict[str, Any]:
        """
        Check the health of all services.
        
        Returns:
            Dict[str, Any]: Health information for all services
        """
        results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "services": {}
        }
        
        for name, config in self.services.items():
            results['services'][name] = self.check_service(name, config)
        
        # Calculate overall health
        healthy_count = sum(1 for service in results['services'].values() if service['status'] == 'healthy')
        total_count = len(results['services'])
        
        results['overall_status'] = 'healthy' if healthy_count == total_count else 'degraded'
        results['healthy_services'] = healthy_count
        results['total_services'] = total_count
        
        return results


class MetricsCollector:
    """Class to collect metrics from the streaming analytics pipeline."""
    
    def __init__(self, config_path: str):
        """
        Initialize the metrics collector with the given configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.metrics_config = self.config.get('metrics', {})
        logger.info(f"Initialized MetricsCollector with config from {config_path}")
    
    def collect_kafka_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from Kafka.
        
        Returns:
            Dict[str, Any]: Kafka metrics
        """
        # In a real implementation, we would use a Kafka client to collect metrics
        # For now, we'll just simulate some metrics
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "topic_metrics": {
                "user-activity": {
                    "messages_per_second": 100.5,
                    "bytes_per_second": 10240.3,
                    "total_messages": 1000000,
                    "partitions": 3,
                    "replication_factor": 1
                },
                "iot-sensors": {
                    "messages_per_second": 50.2,
                    "bytes_per_second": 5120.1,
                    "total_messages": 500000,
                    "partitions": 5,
                    "replication_factor": 1
                },
                "transactions": {
                    "messages_per_second": 20.7,
                    "bytes_per_second": 2048.4,
                    "total_messages": 200000,
                    "partitions": 8,
                    "replication_factor": 1
                }
            },
            "broker_metrics": {
                "active_controllers": 1,
                "offline_partitions": 0,
                "under_replicated_partitions": 0,
                "broker_count": 1
            }
        }
    
    def collect_spark_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from Spark.
        
        Returns:
            Dict[str, Any]: Spark metrics
        """
        # In a real implementation, we would use a Spark client to collect metrics
        # For now, we'll just simulate some metrics
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "application_metrics": {
                "user_activity_processor": {
                    "status": "running",
                    "uptime_seconds": 3600,
                    "cores_used": 2,
                    "memory_used_mb": 1024,
                    "records_processed": 1000000,
                    "records_per_second": 100.5,
                    "processing_delay_ms": 150
                }
            },
            "cluster_metrics": {
                "active_applications": 1,
                "active_drivers": 1,
                "active_executors": 2,
                "total_cores": 4,
                "total_memory_mb": 4096,
                "used_cores": 2,
                "used_memory_mb": 2048
            }
        }
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collect all metrics from the streaming analytics pipeline.
        
        Returns:
            Dict[str, Any]: All metrics
        """
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "kafka": self.collect_kafka_metrics(),
            "spark": self.collect_spark_metrics()
        }


def monitor_services(config_path: str) -> Dict[str, Any]:
    """
    Monitor the health of services in the streaming analytics pipeline.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict[str, Any]: Service health information
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    services = config.get('services', {})
    monitor = ServiceMonitor(services)
    
    return monitor.check_all_services()


def collect_metrics(config_path: str) -> Dict[str, Any]:
    """
    Collect metrics from the streaming analytics pipeline.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict[str, Any]: Metrics
    """
    collector = MetricsCollector(config_path)
    
    return collector.collect_all_metrics()


def send_alerts(config_path: str, data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Send alerts based on the provided data.
    
    Args:
        config_path: Path to the configuration file
        data: Data to include in the alerts
        
    Returns:
        Dict[str, bool]: Results of sending alerts to each channel
    """
    alert_manager = AlertManager(config_path)
    
    return alert_manager.send_alerts(data) 