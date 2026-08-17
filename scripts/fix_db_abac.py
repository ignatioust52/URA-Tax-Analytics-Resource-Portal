with open('core/db_users.py', 'r') as f:
    content = f.read()

funcs = """
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
        \"\"\"
        INSERT INTO user_special_permissions (user_id, permission_key, granted_by, reason, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        \"\"\",
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
"""

content = content + "\n\n" + funcs

with open('core/db_users.py', 'w') as f:
    f.write(content)
