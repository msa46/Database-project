from pony.orm import Database
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
        provider = url.scheme
        logger.debug(f"Using provider: {provider}")
        
        db.bind(provider=provider, user=url.username, password=url.password,
                host=url.hostname, port=url.port, database=url.path[1:])
        logger.debug("Database bind successful")
        
        db.generate_mapping(create_tables=True)
        logger.debug("Database mapping generated successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
