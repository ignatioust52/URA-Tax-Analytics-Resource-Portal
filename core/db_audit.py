from core.db import get_db_connection

def log_event(
    user_email: str,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
) -> None:
    """
    Write one row to activity_audit_log.
    Designed to be called in a fire-and-forget style — never raises.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO activity_audit_log
                        (user_email, action, resource_type, resource_id, detail)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_email, action, resource_type, resource_id, detail),
                )
    except Exception:
        # Logging must never crash the app.
        pass


def get_audit_log(limit: int = 200):
    """
    Return the most recent `limit` audit events, newest first.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, logged_at, user_email, action,
                       resource_type, resource_id, detail
                FROM activity_audit_log
                ORDER BY logged_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
