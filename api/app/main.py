"""
main.py

This is the FastAPI entry point for Fleetalytics. It initializes the web app, 
sets up cross-origin middleware (CORS) for frontend compatibility, sets up 
global metrics middleware for Prometheus monitoring, and establishes the db 
schema on startup (for dev only). It also includes routes for API health checks, 
metrics, and registers routers for the main delivery-related endpoints 
(routes, stops, packages).

This file serves as the primary configuration layer for middleware, startup 
hooks, and global app behavior.
"""
# FastAPI imports
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Standard library imports
import time
import logging

# MySql imports
import mysql.connector
from mysql.connector import Error as MySQLError

# App modules imports
from .database import engine, Base, get_db
from .routers import routes, stops, packages
from .services import metrics
from .config import settings

# Load logger
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
)

# CORS middleware to allow cross-origin requests and enable frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables at startup if they don't exist
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    
    # Check database connection
    if settings.db.is_mysql:
        try:
            # Use a helper function to extract connection details
            conn_details = get_mysql_connection_details(settings.db.processed_uri)
            
            # Test connection
            conn = mysql.connector.connect(**conn_details)
            conn.close()
            
            # Log successful connection (without exposing credentials)
            logger.info(
                f"Successfully connected to MySQL database: "
                f"{conn_details['host']}:{conn_details['port']}/{conn_details['database']}"
            )
        except MySQLError as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            # Continue anyway, as SQLAlchemy will handle connection errors
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (if they didn't exist)")

# Helper function to extract MySQL connection details from the URI
def get_mysql_connection_details(uri):
    # Remove the protocol prefix
    conn_parts = uri.replace('mysql+mysqlconnector://', '').split('/')
    conn_auth = conn_parts[0].split('@')
    
    user_pass = conn_auth[0].split(':')
    host_port = conn_auth[1].split(':')
    
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 3306
    
    database = conn_parts[1].split('?')[0]
    
    return {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': port
    }


# Add middleware to track request timing for metrics
@app.middleware("http")
async def add_metrics(request, call_next):
    # Record start time
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Record metrics (duration and count)
    duration = time.time() - start_time
    metrics.REQUEST_LATENCY.labels(
        method=request.method, 
        path=request.url.path
    ).observe(duration)
    metrics.REQUEST_COUNT.labels(
        method=request.method, 
        path=request.url.path
    ).inc()
    
    return response

# Health check endpoint to confirm the API is running
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "database_type": "MySQL" if "mysql" in settings.DATABASE_URI else "SQLite"}

# Prometheus metrics endpoint for monitoring
@app.get("/metrics", tags=["Metrics"])
def get_metrics():
    return metrics.get_metrics()

# Include routers from separate modules
app.include_router(routes.router)
app.include_router(stops.router)
app.include_router(packages.router)

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)