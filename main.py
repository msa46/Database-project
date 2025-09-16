from typing import Union

from fastapi import FastAPI
from src.database.db import init_db
from src.router.auth import router as auth_router

app = FastAPI(
    title="Pizza Delivery API",
    description="Backend API for pizza delivery system with secure authentication",
    version="1.0.0"
)

# Initialize database
init_db()

# Include authentication router
app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"Hello": "World", "message": "Welcome to Pizza Delivery API"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
