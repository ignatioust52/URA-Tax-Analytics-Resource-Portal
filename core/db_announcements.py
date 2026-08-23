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
            SELECT a.* FROM announcements a
            LEFT JOIN announcement_department_access ada ON a.announcement_id = ada.announcement_id
            WHERE a.is_active = TRUE 
            AND (a.expires_at IS NULL OR a.expires_at > now())
            AND (a.visibility = 'EVERYONE' OR (a.visibility = 'SELECTED_DEPARTMENTS' AND ada.department_id = %s))
            ORDER BY a.published_at DESC
        """
        return _fetch_all_dicts(query, (int(department_id),))
    else:
        query = """
            SELECT a.* FROM announcements a
            WHERE a.is_active = TRUE 
            AND a.visibility = 'EVERYONE'
            AND (a.expires_at IS NULL OR a.expires_at > now())
            ORDER BY a.published_at DESC
        """
        return _fetch_all_dicts(query)

def announcements_get_all():
    query = "SELECT * FROM announcements ORDER BY published_at DESC"
    return _fetch_all_dicts(query)

def announcements_create(title, body, visibility, dept_id_list, published_by, expires_at=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                INSERT INTO announcements (title, body, visibility, published_by, expires_at)
                VALUES (%s, %s, %s, %s, %s) RETURNING announcement_id
            """
            cur.execute(query, (title, body, visibility, published_by, expires_at))
            new_id = cur.fetchone()[0]
            
            if visibility == "SELECTED_DEPARTMENTS" and dept_id_list:
                for d_id in dept_id_list:
                    cur.execute("INSERT INTO announcement_department_access (announcement_id, department_id) VALUES (%s, %s)", (new_id, int(d_id)))
            return new_id

def announcements_update(announcement_id, title, body, visibility, dept_id_list, expires_at, is_active):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                UPDATE announcements 
                SET title = %s, body = %s, visibility = %s, expires_at = %s, is_active = %s
                WHERE announcement_id = %s
            """
            cur.execute(query, (title, body, visibility, expires_at, is_active, int(announcement_id)))
            
            cur.execute("DELETE FROM announcement_department_access WHERE announcement_id = %s", (int(announcement_id),))
            if visibility == "SELECTED_DEPARTMENTS" and dept_id_list:
                for d_id in dept_id_list:
                    cur.execute("INSERT INTO announcement_department_access (announcement_id, department_id) VALUES (%s, %s)", (int(announcement_id), int(d_id)))

def announcements_delete(announcement_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM announcement_department_access WHERE announcement_id = %s", (int(announcement_id),))
            cur.execute("DELETE FROM announcements WHERE announcement_id = %s", (int(announcement_id),))
