import pandas as pd

from core.db import get_connection


def departments_get_all():
    """Returns all departments from the departments table, ordered by name.
    Returns an empty DataFrame if the table doesn't exist yet (pre-migration).
    """
    try:
        conn = get_connection()
        return pd.read_sql("SELECT id, name FROM departments ORDER BY name", conn)
    except Exception:
        return pd.DataFrame(columns=["id", "name"])


def departments_create(name):
    """Insert a new department; returns its id (or the existing id on conflict)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO departments (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name.strip(),),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    return new_id


def departments_update(dept_id, new_name):
    """Renames a department. All existing grants (user & resource) keep
    pointing at the same department_id, so access is preserved through
    the rename automatically."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE departments SET name = %s WHERE id = %s", (new_name.strip(), int(dept_id)))
    conn.commit()
    cur.close()
    
    return True, "Department renamed."


def departments_delete(dept_id):
    """
    Permanently removes a department. Relies on the existing
    ON DELETE CASCADE foreign keys on user_department_access and
    resource_department_access, so any user/resource grants tied to
    this department are cleanly removed along with it — not left orphaned.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM departments WHERE id = %s", (int(dept_id),))
    conn.commit()
    cur.close()
    
    return True, "Department deleted."



def user_department_access_get(user_id):
    """Returns a list of department *names* granted to the given user.
    Returns an empty list if the table doesn't exist yet (pre-migration).
    """
    try:
        conn = get_connection()
        df = pd.read_sql(
            """
            SELECT d.name
            FROM user_department_access uda
            JOIN departments d ON d.id = uda.department_id
            WHERE uda.user_id = %s
            ORDER BY d.name
            """,
            conn,
            params=(int(user_id),),
        )
        return df["name"].tolist()
    except Exception:
        return []


def user_department_access_set(user_id, dept_id_list):
    """Replace all department-access rows for user_id with the given list of dept IDs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_department_access WHERE user_id = %s", (int(user_id),))
    for dept_id in dept_id_list:
        cur.execute(
            "INSERT INTO user_department_access (user_id, department_id) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (int(user_id), int(dept_id)),
        )
    conn.commit()
    cur.close()
    



def resource_department_access_get(resource_id):
    """Returns a list of department *names* granted to the given resource.
    An empty list means 'visible to everyone' when combined with the
    legacy department == 'All' convention.
    """
    try:
        conn = get_connection()
        df = pd.read_sql(
            """
            SELECT d.name
            FROM resource_department_access rda
            JOIN departments d ON d.id = rda.department_id
            WHERE rda.resource_id = %s
            ORDER BY d.name
            """,
            conn,
            params=(int(resource_id),),
        )
        return df["name"].tolist()
    except Exception:
        return []


def resource_department_access_set(resource_id, dept_id_list):
    """Replace all department-access rows for resource_id with the given list of dept IDs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM resource_department_access WHERE resource_id = %s", (int(resource_id),))
    for dept_id in dept_id_list:
        cur.execute(
            "INSERT INTO resource_department_access (resource_id, department_id) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (int(resource_id), int(dept_id)),
        )
    conn.commit()
    cur.close()
    



def resources_get_department_map():
    """Returns {resource_id: [department names]} for every resource that has
    specific department access rows. Resources with no rows here are visible
    to everyone (assuming their legacy department column is 'All').
    """
    try:
        conn = get_connection()
        df = pd.read_sql(
            """
            SELECT rda.resource_id, d.name
            FROM resource_department_access rda
            JOIN departments d ON d.id = rda.department_id
            """,
            conn,
        )
        result = {}
        for rid, group in df.groupby("resource_id"):
            result[int(rid)] = sorted(group["name"].tolist())
        return result
    except Exception:
        return {}


