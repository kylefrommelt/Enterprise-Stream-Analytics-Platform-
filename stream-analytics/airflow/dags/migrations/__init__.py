"""
Database migration system for the streaming analytics pipeline.
"""

from alembic import command
from alembic.config import Config
import os

def get_alembic_config():
    """Get Alembic configuration."""
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", os.path.dirname(__file__))
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/stream_analytics"))
    return alembic_cfg

def run_migrations():
    """Run database migrations."""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head") 