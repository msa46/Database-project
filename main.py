from typing import Union

from fastapi import FastAPI
from src.database.db import init_db

app = FastAPI()

print("Initializing database...")
init_db()
print("Database initialization complete.")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
