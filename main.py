from typing import Union
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.db import init_db
from src.router.auth import router as auth_router
from src.router.secured import router as secured_router

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pizza Delivery API",
    description="Backend API for pizza delivery system with secure authentication",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Allow both localhost and 127.0.0.1
    allow_credentials=True,  # Changed to True to support credentials if needed
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add middleware to log all requests for debugging
@app.middleware("http")
async def log_requests(request, call_next):
    origin = request.headers.get("origin")
    logger.debug(f"Incoming request: {request.method} {request.url}")
    logger.debug(f"Origin: {origin}")
    logger.debug(f"Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    # Log CORS-related headers
    cors_headers = {
        "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
        "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
        "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
        "access-control-max-age": response.headers.get("access-control-max-age"),
        "vary": response.headers.get("vary")
    }
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"CORS headers: {cors_headers}")
    logger.debug(f"All response headers: {dict(response.headers)}")
    
    return response

# Initialize database
logger.debug("Initializing database...")
try:
    init_db()
    logger.debug("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    raise

# Include authentication router
logger.debug("Including authentication router")
app.include_router(auth_router)

# Include secured router
logger.debug("Including secured router")
app.include_router(secured_router)


@app.get("/")
def read_root():
    return {"Hello": "World", "message": "Welcome to Pizza Delivery API"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
