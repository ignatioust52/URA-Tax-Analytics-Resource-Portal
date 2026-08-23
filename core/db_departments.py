from core.db import get_db_connection

def _fetch_all_dicts(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

def departments_get_all():
    """Returns all departments from the departments table, ordered by name."""
    try:
        return _fetch_all_dicts("SELECT id, name FROM departments ORDER BY name")
    except Exception:
        return []

def departments_create(name):
    """Insert a new department; returns its id (or the existing id on conflict)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO departments (name) VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                (name.strip(),),
            )
            return cur.fetchone()[0]

def departments_update(dept_id, new_name):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE departments SET name = %s WHERE id = %s", (new_name.strip(), int(dept_id)))
    return True, "Department renamed."

def departments_delete(dept_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM departments WHERE id = %s", (int(dept_id),))
    return True, "Department deleted."

def user_department_access_get(user_id):
    """Returns a list of department *names* granted to the given user."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT d.name
                    FROM user_department_access uda
                    JOIN departments d ON d.id = uda.department_id
                    WHERE uda.user_id = %s
                    ORDER BY d.name
                    """,
                    (int(user_id),)
                )
                return [row[0] for row in cur.fetchall()]
    except Exception:
        return []

def user_department_access_set(user_id, dept_id_list):
    """Replace all department-access rows for user_id with the given list of dept IDs."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_department_access WHERE user_id = %s", (int(user_id),))
            for dept_id in dept_id_list:
                cur.execute(
                    "INSERT INTO user_department_access (user_id, department_id) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (int(user_id), int(dept_id)),
                )

def resource_department_access_get(resource_id):
    """Returns a list of department *names* granted to the given resource."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT d.name
                    FROM resource_department_access rda
                    JOIN departments d ON d.id = rda.department_id
                    WHERE rda.resource_id = %s
                    ORDER BY d.name
                    """,
                    (int(resource_id),)
                )
                return [row[0] for row in cur.fetchall()]
    except Exception:
        return []

def resource_department_access_set(resource_id, dept_id_list):
    """Replace all department-access rows for resource_id with the given list of dept IDs."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM resource_department_access WHERE resource_id = %s", (int(resource_id),))
            for dept_id in dept_id_list:
                cur.execute(
                    "INSERT INTO resource_department_access (resource_id, department_id) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (int(resource_id), int(dept_id)),
                )

def resources_get_department_map():
    """Returns {resource_id: [department names]} for every resource."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT rda.resource_id, d.name
                    FROM resource_department_access rda
                    JOIN departments d ON d.id = rda.department_id
                    """
                )
                result = {}
                for rid, name in cur.fetchall():
                    rid = int(rid)
                    if rid not in result:
                        result[rid] = []
                    result[rid].append(name)
                for rid in result:
                    result[rid].sort()
                return result
    except Exception:
        return {}
