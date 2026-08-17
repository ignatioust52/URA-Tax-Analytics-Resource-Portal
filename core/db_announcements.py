import pandas as pd
import streamlit as st
from core.db import get_connection

@st.cache_data(ttl=60)
def announcements_get_active(department_id=None):
    conn = get_connection()
    # Fetch active announcements where audience_department_id is null (global) or matches user department
    if department_id:
        query = """
            SELECT * FROM announcements 
            WHERE is_active = TRUE 
            AND (audience_department_id IS NULL OR audience_department_id = %s)
            AND (expires_at IS NULL OR expires_at > now())
            ORDER BY published_at DESC
        """
        df = pd.read_sql(query, conn, params=(department_id,))
    else:
        query = """
            SELECT * FROM announcements 
            WHERE is_active = TRUE 
            AND audience_department_id IS NULL
            AND (expires_at IS NULL OR expires_at > now())
            ORDER BY published_at DESC
        """
        df = pd.read_sql(query, conn)
    return df

@st.cache_data(ttl=60)
def announcements_get_all():
    conn = get_connection()
    query = "SELECT * FROM announcements ORDER BY published_at DESC"
    return pd.read_sql(query, conn)

def announcements_create(title, body, audience_department_id, published_by, expires_at=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO announcements (title, body, audience_department_id, published_by, expires_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(query, (title, body, audience_department_id, published_by, expires_at))
    conn.commit()
    announcements_get_all.clear()
    announcements_get_active.clear()

def announcements_update(announcement_id, title, body, audience_department_id, expires_at, is_active):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        UPDATE announcements 
        SET title = %s, body = %s, audience_department_id = %s, expires_at = %s, is_active = %s
        WHERE announcement_id = %s
    """
    cur.execute(query, (title, body, audience_department_id, expires_at, is_active, announcement_id))
    conn.commit()
    announcements_get_all.clear()
    announcements_get_active.clear()

def announcements_delete(announcement_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM announcements WHERE announcement_id = %s", (announcement_id,))
    conn.commit()
    announcements_get_all.clear()
    announcements_get_active.clear()
