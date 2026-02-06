import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from urllib.parse import urlparse

load_dotenv()

def get_db_config():
    """Get database configuration from environment"""
    # Render provides DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Parse Render's DATABASE_URL
        result = urlparse(database_url)
        return {
            'dbname': result.path[1:],  # Remove leading '/'
            'user': result.username,
            'password': result.password,
            'host': result.hostname,
            'port': result.port or 5432
        }
    else:
        # Local development using .env
        return {
            'dbname': os.getenv("DB_NAME"),
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'host': os.getenv("DB_HOST"),
            'port': int(os.getenv("DB_PORT", 5432))
        }

# Get database config
db_config = get_db_config()

# Create a connection pool
psql_pool = pool.SimpleConnectionPool(
    1, 10,
    **db_config
)

def psql(query, params=None, fetch=True):
    """
    Run a query with optional parameters.
    - query: SQL string (use %s placeholders!)
    - params: tuple of values for placeholders
    - fetch: whether to fetch results (default True)
    """
    conn = psql_pool.getconn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query, params)
    conn.commit()
    data = None
    if fetch:
        try:
            data = cur.fetchall()
        except psycopg2.ProgrammingError:
            pass
    cur.close()
    psql_pool.putconn(conn)
    return data