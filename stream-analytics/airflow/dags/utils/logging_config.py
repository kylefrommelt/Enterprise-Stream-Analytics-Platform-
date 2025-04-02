"""
Logging configuration for the streaming analytics pipeline.
"""

import logging
import logging.config
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes additional context."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
            
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logging(log_level: str = 'INFO') -> None:
    """Configure logging with JSON formatting and file handlers."""
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': CustomJsonFormatter,
                'format': '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d %(funcName)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'level': log_level,
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'json',
                'level': log_level,
                'filename': 'logs/stream_analytics.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True
            },
            'stream_analytics': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(f'stream_analytics.{name}') 