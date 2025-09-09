from pony.orm import Database
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

db = Database()

def init_db(conn_string=None):
    load_dotenv()
    if conn_string is None:
        conn_string = os.getenv("DB_CONN_STRING")

    url = urlparse(conn_string)
    db.bind(provider=url.scheme, user=url.username, password=url.password,
            host=url.hostname, port=url.port, database=url.path[1:])
    db.generate_mapping(create_tables=True)