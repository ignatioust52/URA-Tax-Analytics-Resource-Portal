from core.db import get_db_connection

def _fetch_all_dicts(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

def announcements_get_active(department_id=None):
    if department_id:
        query = """
            SELECT * FROM announcements 
            WHERE is_active = TRUE 
            AND (audience_department_id IS NULL OR audience_department_id = %s)
            AND (expires_at IS NULL OR expires_at > now())
            ORDER BY published_at DESC
        """
        return _fetch_all_dicts(query, (department_id,))
    else:
        query = """
            SELECT * FROM announcements 
            WHERE is_active = TRUE 
            AND audience_department_id IS NULL
            AND (expires_at IS NULL OR expires_at > now())
            ORDER BY published_at DESC
        """
        return _fetch_all_dicts(query)


def announcements_get_all():
    query = "SELECT * FROM announcements ORDER BY published_at DESC"
    return _fetch_all_dicts(query)

def announcements_create(title, body, audience_department_id, published_by, expires_at=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                INSERT INTO announcements (title, body, audience_department_id, published_by, expires_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(query, (title, body, audience_department_id, published_by, expires_at))


def announcements_update(announcement_id, title, body, audience_department_id, expires_at, is_active):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                UPDATE announcements 
                SET title = %s, body = %s, audience_department_id = %s, expires_at = %s, is_active = %s
                WHERE announcement_id = %s
            """
            cur.execute(query, (title, body, audience_department_id, expires_at, is_active, announcement_id))


def announcements_delete(announcement_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM announcements WHERE announcement_id = %s", (announcement_id,))
