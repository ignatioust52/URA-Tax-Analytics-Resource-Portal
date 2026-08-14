"""
core/db_audit.py — Activity audit log (DB layer).

Borrowed concept from the reference app's audit_logs table and
AdminAuditPage — every significant user action is recorded so admins
can see who did what and when.

Public API:
  log_event(user_email, action, resource_type=None, resource_id=None, detail=None)
      Fire-and-forget write. Swallows exceptions so a logging failure
      never crashes the UI.

  get_audit_log(limit=200)
      Returns a DataFrame of the most recent events, newest first.
      For admin display only.
"""

import pandas as pd

from core.db import get_connection


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
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO activity_audit_log
                (user_email, action, resource_type, resource_id, detail)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_email, action, resource_type, resource_id, detail),
        )
        conn.commit()
        cur.close()
    except Exception:
        # Logging must never crash the app.
        pass


def get_audit_log(limit: int = 200) -> pd.DataFrame:
    """
    Return the most recent `limit` audit events, newest first.
    Columns: id, logged_at, user_email, action, resource_type, resource_id, detail
    """
    conn = get_connection()
    return pd.read_sql(
        """
        SELECT id, logged_at, user_email, action,
               resource_type, resource_id, detail
        FROM activity_audit_log
        ORDER BY logged_at DESC
        LIMIT %s
        """,
        conn,
        params=[limit],
    )
