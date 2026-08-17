import os
import psycopg2
import streamlit as st

@st.cache_resource
def _create_connection():
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        st.error(f"Missing database environment variables: {', '.join(missing)}. Check your .env file.")
        st.stop()
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = '180000';")  # 3 minutes
    return conn

def get_connection():
    conn = _create_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        st.cache_resource.clear()
        conn = _create_connection()
    return conn
