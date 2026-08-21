"""
core/db_users.py — App user account management (DB layer).

All functions that read or write the app_users table live here.
The RBAC model is binary: role is 'admin' or NULL/non-admin.
users_approve / users_toggle_active / users_delete all enforce the
"at least one active admin must remain" safeguard at the DB layer.
"""

import bcrypt
import pandas as pd


from core.db import get_connection
from core.db_departments import user_department_access_set


def user_get_by_email(email):
    """Fetch user by email."""
    if not email:
        return None
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM app_users WHERE LOWER(email) = LOWER(%s)",
        conn,
        params=(email,)
    )
    if df.empty:
        return None
    return df.iloc[0].to_dict()



def users_get_all():
    """Returns all non-pending users (active + disabled) ordered by id."""
    conn = get_connection()
    return pd.read_sql(
        "SELECT u.id, u.email, r.name as role, u.department, u.status, u.is_active, u.created_at FROM app_users u LEFT JOIN roles r ON u.role_id = r.role_id "
        "WHERE status != 'pending' ORDER BY id",
        conn,
    )


def users_get_pending():
    """Returns all accounts waiting for admin approval.
    Returns an empty DataFrame if the status column doesn't exist yet (pre-migration).
    """
    try:
        conn = get_connection()
        return pd.read_sql(
            "SELECT u.id, u.email, u.requested_department, u.created_at FROM app_users u "
            "WHERE status = 'pending' ORDER BY created_at",
            conn,
        )
    except Exception:
        return pd.DataFrame(columns=["id", "email", "requested_department", "created_at"])


def users_create(email, password_raw, role, dept_id_list, status="active"):
    """
    Admin-path account creation — bypasses the self-registration queue.
    role         : role name string, e.g. 'admin' or 'viewer'.
    dept_id_list : list of department IDs to grant access immediately.
    status       : 'active' for admin-created accounts (default).
    """
    hashed = bcrypt.hashpw(password_raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    cur = conn.cursor()
    is_active = (status == "active")
    # Look up the role_id from the roles table by name (case-insensitive).
    cur.execute("SELECT role_id FROM roles WHERE LOWER(name) = LOWER(%s)", (role,))
    role_row = cur.fetchone()
    role_id = role_row[0] if role_row else None
    cur.execute(
        """
        INSERT INTO app_users (email, password_hash, role_id, role, department, is_active, status)
        VALUES (%s, %s, %s, %s, '', %s, %s)
        RETURNING id
        """,
        (email.strip().lower(), hashed, role_id, role.lower() if role else None, is_active, status),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    if dept_id_list:
        user_department_access_set(new_id, dept_id_list)
    
    return new_id


def users_register(email, password_raw, requested_department):
    """
    Self-registration path. Creates a pending account with role=NULL.
    requested_department : string the user typed/selected — stored for admin
    reference only; does NOT auto-create a row in the departments table.
    """
    hashed = bcrypt.hashpw(password_raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO app_users
            (email, password_hash, role_id, role, department, is_active, status, requested_department)
        VALUES (%s, %s, NULL, NULL, '', FALSE, 'pending', %s)
        RETURNING id
        """,
        (email.strip().lower(), hashed, requested_department),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return new_id


def users_approve(user_id, role, dept_id_list):
    """
    Approve a pending user: set status='active', is_active=TRUE, assign role,
    and grant department access via user_department_access.
    Both role_id (FK) and legacy role (varchar) are kept in sync.
    """
    conn = get_connection()
    cur = conn.cursor()
    # Look up role_id from roles table
    cur.execute("SELECT role_id FROM roles WHERE LOWER(name) = LOWER(%s)", (role,))
    role_row = cur.fetchone()
    role_id = role_row[0] if role_row else None
    cur.execute(
        """
        UPDATE app_users
        SET status = 'active', is_active = TRUE, role_id = %s, role = %s
        WHERE id = %s
        """,
        (role_id, role.lower() if role else None, int(user_id)),
    )
    conn.commit()
    cur.close()
    user_department_access_set(int(user_id), dept_id_list)
    


def users_reject(user_id):
    """
    Reject a pending user: set status='disabled', is_active=FALSE.
    The row is KEPT (not deleted) intentionally:
      - Maintains an audit trail of who applied and was rejected.
      - Prevents the same email from re-registering without admin awareness.
      - Allows the admin to undo a mistaken rejection by re-enabling later.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE app_users SET status = 'disabled', is_active = FALSE WHERE id = %s",
        (int(user_id),),
    )
    conn.commit()
    cur.close()
    


def users_toggle_active(user_id):
    """
    Toggle is_active for the given user and mirror the change into status
    ('active' / 'disabled') so both fields stay in sync.
    Blocks disabling the last active admin account.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT r.name as role, u.is_active FROM app_users u LEFT JOIN roles r ON u.role_id = r.role_id WHERE u.id = %s", (int(user_id),))
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        return False, "User account not found."

    target_role, target_active = user_row[0], user_row[1]

    if target_role == "admin" and target_active:
        cur.execute("SELECT COUNT(*) FROM app_users u JOIN roles r ON u.role_id = r.role_id WHERE LOWER(r.name) = 'admin' AND u.is_active = TRUE")
        active_admins = cur.fetchone()[0]
        if active_admins <= 1:
            cur.close()
            return False, "Cannot disable the only remaining active admin account. At least one active admin must remain."

    new_active = not target_active
    new_status = "active" if new_active else "disabled"
    cur.execute(
        "UPDATE app_users SET is_active = %s, status = %s WHERE id = %s",
        (new_active, new_status, int(user_id)),
    )
    conn.commit()
    cur.close()
    
    return True, "Updated user account status."


def users_delete(user_id):
    """
    Permanently removes a user account. Blocks deleting the only remaining
    active admin, same safeguard as users_toggle_active.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT r.name as role, u.is_active FROM app_users u LEFT JOIN roles r ON u.role_id = r.role_id WHERE u.id = %s", (int(user_id),))
    row = cur.fetchone()
    if not row:
        cur.close()
        return False, "User account not found."

    target_role, target_active = row[0], row[1]
    if target_role == "admin" and target_active:
        cur.execute("SELECT COUNT(*) FROM app_users u JOIN roles r ON u.role_id = r.role_id WHERE LOWER(r.name) = 'admin' AND u.is_active = TRUE")
        active_admins = cur.fetchone()[0]
        if active_admins <= 1:
            cur.close()
            return False, "Cannot delete the only remaining active admin account."

    try:
        cur.execute("DELETE FROM public_resource_recent WHERE user_id = %s", (int(user_id),))
        cur.execute("DELETE FROM public_resource_favorites WHERE user_id = %s", (int(user_id),))
        cur.execute("DELETE FROM user_sessions WHERE user_id = %s", (int(user_id),))
        cur.execute("DELETE FROM user_department_access WHERE user_id = %s", (int(user_id),))
        cur.execute("DELETE FROM user_special_permissions WHERE user_id = %s", (int(user_id),))
        cur.execute("DELETE FROM app_users WHERE id = %s", (int(user_id),))
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        return False, f"Failed to delete user: {str(e)}"
    
    cur.close()
    
    return True, "User account deleted."


def users_update_role_department(user_id, role, dept_id_list):
    """
    Updates a user's role and replaces their department access list.
    Blocks demoting the only remaining active admin away from 'admin'.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT r.name as role, u.is_active FROM app_users u LEFT JOIN roles r ON u.role_id = r.role_id WHERE u.id = %s", (int(user_id),))
    row = cur.fetchone()
    if not row:
        cur.close()
        return False, "User account not found."

    current_role, is_active_flag = row[0], row[1]
    if current_role == "admin" and is_active_flag and role != "admin":
        cur.execute("SELECT COUNT(*) FROM app_users u JOIN roles r ON u.role_id = r.role_id WHERE LOWER(r.name) = 'admin' AND u.is_active = TRUE")
        active_admins = cur.fetchone()[0]
        if active_admins <= 1:
            cur.close()
            return False, "Cannot change role — this is the only remaining active admin."

    cur.execute("UPDATE app_users SET role_id = (SELECT role_id FROM roles WHERE LOWER(name) = LOWER(%s)) WHERE id = %s", (role, int(user_id)))
    conn.commit()
    cur.close()
    user_department_access_set(int(user_id), dept_id_list)
    
    return True, "User role and department access updated."


def users_reset_password(user_id, new_password_raw):
    """Admin-initiated password reset — hashes and stores a new password."""
    hashed = bcrypt.hashpw(new_password_raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE app_users SET password_hash = %s WHERE id = %s", (hashed, int(user_id)))
    conn.commit()
    cur.close()
    return True, "Password reset successfully."



def users_get_special_permissions(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, permission_key, granted_by, reason, expires_at FROM user_special_permissions WHERE user_id = %s", (int(user_id),))
    perms = []
    for row in cur.fetchall():
        perms.append({
            "id": row[0],
            "permission_key": row[1],
            "granted_by": row[2],
            "reason": row[3],
            "expires_at": row[4]
        })
    cur.close()
    return perms

def users_grant_special_permission(user_id, permission_key, granted_by, reason=None, expires_at=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_special_permissions (user_id, permission_key, granted_by, reason, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (int(user_id), permission_key, int(granted_by) if granted_by else None, reason, expires_at)
    )
    conn.commit()
    cur.close()

def users_revoke_special_permission(perm_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_special_permissions WHERE id = %s", (int(perm_id),))
    conn.commit()
    cur.close()
