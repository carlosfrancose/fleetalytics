"""
database.py

This module configures the database layer for Fleetalytics API. It initializes 
the SQLAlchemy engine, session factory, and declarative base for models to 
inherit. It also provides a FastAPI dependency ('get_db') that can be used for 
managing database sessions within API endpoints.

The database URI is read from environment variables and supports both SQLite 
(default for dev) and MySQL (production-ready). If MySQL is detected, additional
engine options are configured to handle pooling and compatibility using the 
mysql+mysqlconnector dialect.

This module is imported early in the app's lifecycle to ensure models and
sessions are properly configured before any API routes or events are executed.
"""
# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Standard library imports
import os
import logging

# .env import
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load logger
logger = logging.getLogger(__name__)

# Get database connection string from environment variable
# Use a default SQLite connection for development if not provided
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///./fleetalytics.db")

# If using MySQL, specify mysql+mysqlconnector as the dialect
if DATABASE_URI.startswith('mysql:'):
    # Replace mysql: with mysql+mysqlconnector:
    DATABASE_URI = DATABASE_URI.replace('mysql:', 'mysql+mysqlconnector:')

# Logging database type
logger.info(f"Using database: {'MySQL+mysqlconnector' if 'mysql+mysqlconnector' in DATABASE_URI else 'SQLite'}")

# Create arguements for SQLAlchemy engine
engine_args = {
    "echo": False,  # Set to True for debugging
    "pool_pre_ping": True,  # Verify connection before using it
}

# Add MySQL-specific connection arguments if using MySQL
if 'mysql+mysqlconnector' in DATABASE_URI:
    engine_args.update({
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle connections after 1 hour
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),  # Connection pool size
        "connect_args": {
            "use_pure": True    # Use pure Python implementation
        }
    })

# Create engine with appropriate arguments
engine = create_engine(DATABASE_URI, **engine_args)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """
    Creates and yields a database session.
    
    This is a dependency that can be used in FastAPI endpoints to get a database 
    session. The session is automatically closed when the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()