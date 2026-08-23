import bcrypt
import secrets
from datetime import datetime, timezone

from core.db import get_db_connection

# Configuration
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour

def is_password_strong(password):
    """Returns (is_valid, message). Minimum: 8 chars, 1 letter, 1 number."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""


def user_get_by_email(email):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT u.id, u.email, u.password_hash, u.department, u.status, u.is_active, 
                       r.name as role_name, r.hierarchy_level 
                FROM app_users u 
                LEFT JOIN roles r ON u.role_id = r.role_id 
                WHERE u.email = %s
            """
            cur.execute(query, (email.strip().lower(),))
            row = cur.fetchone()
            if not row:
                return None
            
            # Reconstruct dictionary from row
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))


def create_user_session(user_id):
    token = secrets.token_urlsafe(32)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_sessions (token, user_id, last_activity_at) VALUES (%s, %s, NOW())",
                (token, int(user_id)),
            )
    return token


def get_active_session(token):
    """Returns the session+user row if the token is valid, active, and not
    timed out — otherwise deletes it (if present) and returns None."""
    if not token:
        return None
        
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT us.token, us.user_id, us.last_activity_at,
                       u.id, u.email, u.role, u.department, u.status, u.is_active,
                       r.name as role_name
                FROM user_sessions us
                JOIN app_users u ON u.id = us.user_id
                LEFT JOIN roles r ON u.role_id = r.role_id
                WHERE us.token = %s
                """,
                (token,)
            )
            row = cur.fetchone()
            if not row:
                return None
            
            cols = [desc[0] for desc in cur.description]
            session = dict(zip(cols, row))

    last_activity = session["last_activity_at"]
    # Handle timezone differences (last_activity might be naive from DB or aware)
    now = datetime.now(timezone.utc)
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)
        
    elapsed = (now - last_activity).total_seconds()

    if elapsed > SESSION_TIMEOUT_SECONDS or session["status"] != "active" or not bool(session["is_active"]):
        delete_user_session(token)
        return None
        
    # Normalize: always expose a lowercase 'role' derived from the roles table.
    role_name = session.get("role_name") or session.get("role") or ""
    session["role"] = role_name.lower()
    
    return session


def touch_user_session(token):
    """Resets the idle clock — called on every authenticated interaction."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE user_sessions SET last_activity_at = NOW() WHERE token = %s", (token,))


def delete_user_session(token):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_sessions WHERE token = %s", (token,))

# Note: check_login() has been completely removed as it was legacy Streamlit UI code.