"""
config.py

This module centralizes application configurations using Pydantic's BaseSettings 
class and pulling values from environment variables (via .env).

It loads configurations for:
- Logger (log level, format)
- Database (supporting SQLite and MySQL)
- FastAPI (host, port, debug mode)
- Other metadata used throughout the app

On import, it initializes a global 'settings' object to be used across the 
application for consistent access to configuration values.
"""
import os
import logging
from dotenv import load_dotenv
from pydantic import BaseSettings

# Load environment variables
load_dotenv()

# Configure logging for the entire application
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

"""
    Database Settings:
    This class handles database-specific configurations and properties such as 
    connection URI, pooling options, and dialect handling.
"""
class DatabaseSettings(BaseSettings):
    RAW_URI: str = os.getenv("DATABASE_URI", "sqlite:///./fleetalytics.db")
    # SQLAlchemy settings
    POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "True").lower() in ("true", "1", "t")
    ECHO: bool = os.getenv("DB_ECHO", "False").lower() in ("true", "1", "t")
    ECHO_POOL: bool = os.getenv("DB_ECHO_POOL", "False").lower() in ("true", "1", "t")
    # MySQL settings
    POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    
    # Adjust raw URI for mysql-connector-python if needed
    @property
    def processed_uri(self):
        uri = self.RAW_URI
        if uri.startswith('mysql:'):
            uri = uri.replace('mysql:', 'mysql+mysqlconnector:')
        return uri

    # Check if the database is MySQL
    @property
    def is_mysql(self):
        return 'mysql' in self.processed_uri
    
    # Create SQLAlchemy arguments based on the database type
    @property
    def engine_args(self):
        args = {
            "pool_pre_ping": self.POOL_PRE_PING,
            "echo": self.ECHO,
            "echo_pool": self.ECHO_POOL,
        }
        
        # Add MySQL-specific arguments if using MySQL
        if self.is_mysql:
            args.update({
                "pool_size": self.POOL_SIZE,
                "max_overflow": self.MAX_OVERFLOW,
                "pool_recycle": self.POOL_RECYCLE,
                "connect_args": {
                    "use_pure": True  # Use pure Python implementation
                }
            })
        
        return args

"""
    Application settings: 
    This class handles application-wide settings such as API host, port, 
    debug mode, and other metadata. It also initializes the database settings.
"""
class Settings(BaseSettings):
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Application metadata
    APP_NAME: str = "Fleetalytics API"
    APP_DESCRIPTION: str = "API for delivery routes, stops, and packages."
    APP_VERSION: str = "0.1.0"
    
    # Database settings
    db: DatabaseSettings = DatabaseSettings()
    
    # Pydantic config
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings object
settings = Settings()

# Log the configuration at startup
logger.info(f"API running in {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")
logger.info(f"Database type: {'MySQL' if settings.db.is_mysql else 'SQLite'}")
if settings.db.is_mysql:
    # Extract and log database host (obscure sensitive parts)
    db_parts = settings.db.processed_uri.split('@')
    if len(db_parts) > 1:
        db_host = db_parts[1].split('/')[0]
        logger.info(f"Database host: {db_host}")
        logger.info(f"Pool size: {settings.db.POOL_SIZE}, Pool recycle: {settings.db.POOL_RECYCLE}")