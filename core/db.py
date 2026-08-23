import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool = None

def init_db_pool():
    global _db_pool
    if _db_pool is not None:
        return
        
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing DB env vars: {', '.join(missing)}")
        
    try:
        _db_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 20,
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
            dbname=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD")
        )
        logger.info("Database connection pool initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise

@contextmanager
def get_db_connection():
    """
    Context manager that yields a database connection from the pool
    and automatically returns it when done.
    """
    global _db_pool
    if _db_pool is None:
        init_db_pool()
        
    conn = _db_pool.getconn()
    try:
        conn.autocommit = True
        yield conn
    finally:
        if _db_pool is not None:
            _db_pool.putconn(conn)

def get_connection():
    """
    DEPRECATED: Legacy function for backwards compatibility during migration.
    Returns a connection from the pool.
    WARNING: The caller MUST manually close the connection to return it to the pool.
    Use `with get_db_connection() as conn:` instead.
    """
    global _db_pool
    if _db_pool is None:
        init_db_pool()
    conn = _db_pool.getconn()
    conn.autocommit = True
    return conn

def release_connection(conn):
    """Legacy helper to release connections fetched via get_connection()"""
    global _db_pool
    if _db_pool is not None and conn is not None:
        _db_pool.putconn(conn)
