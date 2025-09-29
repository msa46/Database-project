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
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

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
