from pony.orm import Database, db_session
from urllib.parse import urlparse
import os
import logging
from dotenv import load_dotenv

db = Database()

def init_db(conn_string=None):
    # Import models here to ensure they are registered with db before mapping
    from . import models
    
    logger = logging.getLogger(__name__)
    logger.debug("Initializing database...")

    load_dotenv()
    if conn_string is None:
        conn_string = os.getenv("DB_CONN_STRING")
        logger.debug(f"DB_CONN_STRING from env: {conn_string[:20]}..." if conn_string else "None")

    if not conn_string:
        logger.error("Database connection string is None or empty")
        raise ValueError("Database connection string is required")

    try:
        url = urlparse(conn_string)
        logger.debug(f"Parsed URL - scheme: {url.scheme}, host: {url.hostname}, port: {url.port}, db: {url.path[1:]}")
        
        # Pony ORM uses 'postgres' as the provider name
        # Handle both postgresql:// and postgres:// schemes
        provider = url.scheme
        if provider == 'postgresql':
            provider = 'postgres'
        logger.debug(f"Using provider: {provider}")
        
        # Test database connection with detailed error logging
        logger.debug("Attempting to bind to database...")
        db.bind(provider=provider, user=url.username, password=url.password,
                host=url.hostname, port=url.port, database=url.path[1:])
        logger.debug("Database bind successful")
        
        logger.debug("Generating database mapping...")
        db.generate_mapping(create_tables=True)
        logger.debug("Database mapping generated successfully")
        
        # Test a simple query to verify connection
        logger.debug("Testing database connection with simple query...")
        with db_session:
            # Just test if we can access the database
            test_query = "SELECT 1"
            db.execute(test_query)
        logger.debug("Database connection test successful")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
