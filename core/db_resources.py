import pandas as pd
import streamlit as st
from core.db import get_connection
from core.db_departments import resource_department_access_set


@st.cache_data(ttl=60)
def resources_get_all():
    conn = get_connection()
    query = """
        SELECT
            id,
            COALESCE(NULLIF(page_name, ''), page, '') AS page_name,
            COALESCE(NULLIF(business_name, ''), business, '') AS business_name,
            description,
            category,
            url,
            COALESCE(admin_only, false) AS admin_only,
            COALESCE(NULLIF(department, ''), 'All') AS department,
            added_by,
            last_edited_by,
            created_at,
            updated_at,
            COALESCE(view_count, 0) AS view_count,
            last_viewed_at,
            approval_status,
            sensitivity_classification
        FROM public_resources
        ORDER BY id
    """
    try:
        return pd.read_sql(query, conn)
    except Exception:
        return pd.read_sql("SELECT * FROM public_resources ORDER BY id", conn)


def resources_create(page_name, business_name, description, category, url, admin_only, dept_id_list, added_by):
    department = "All" if not dept_id_list else ""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO public_resources (page_name, business_name, description, category, url, admin_only, department, added_by, approval_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PendingApproval')
        RETURNING id
        """,
        (page_name, business_name, description, category, url, admin_only, department, added_by),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    resource_department_access_set(new_id, dept_id_list)
    resources_log_audit(new_id, "create", added_by, f"Created '{business_name}'")
    resources_get_all.clear()
    return new_id


def resources_update(resource_id, page_name, business_name, description, category, url, admin_only, dept_id_list, last_edited_by):
    department = "All" if not dept_id_list else ""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE public_resources
        SET page_name = %s, business_name = %s, description = %s, category = %s,
            url = %s, admin_only = %s, department = %s, last_edited_by = %s
        WHERE id = %s
        """,
        (page_name, business_name, description, category, url, admin_only, department, last_edited_by, int(resource_id)),
    )
    conn.commit()
    cur.close()
    resource_department_access_set(int(resource_id), dept_id_list)
    resources_log_audit(int(resource_id), "update", last_edited_by, f"Updated '{business_name}'")
    resources_get_all.clear()


def resources_delete(resource_id, business_name, deleted_by):
    resources_log_audit(int(resource_id), "delete", deleted_by, f"Deleted '{business_name}'")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM public_resource_recent WHERE resource_id = %s", (int(resource_id),))
        cur.execute("DELETE FROM public_resource_favorites WHERE resource_id = %s", (int(resource_id),))
        cur.execute("DELETE FROM resource_department_access WHERE resource_id = %s", (int(resource_id),))
        cur.execute("DELETE FROM public_resources WHERE id = %s", (int(resource_id),))
        conn.commit()
        resources_get_all.clear()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()


def resources_record_view(resource_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE public_resources SET view_count = view_count + 1, last_viewed_at = NOW() WHERE id = %s",
        (int(resource_id),),
    )
    conn.commit()
    cur.close()


def test_resource_url(url):
    import requests
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "❌ Only http/https URLs are allowed."

    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    hostname = (parsed.hostname or "").lower()
    if hostname in blocked_hosts or hostname.startswith("169.254.") or hostname.startswith("10.") \
            or hostname.startswith("192.168.") or hostname.startswith("172."):
        return False, "❌ URLs pointing to internal/private addresses are not allowed."

    try:
        resp = requests.get(url, timeout=8, allow_redirects=True)
        if resp.status_code < 400:
            return True, f"✅ Responded with status {resp.status_code}"
        return False, f"⚠️ Responded with status {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "❌ Timed out after 8 seconds"
    except requests.exceptions.ConnectionError:
        return False, "❌ Could not connect (DNS or connection error)"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Request failed: {e}"




def resources_log_audit(resource_id, action, changed_by, details=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO public_resources_audit_log (resource_id, action, changed_by, details) VALUES (%s, %s, %s, %s)",
        (resource_id, action, changed_by or "unknown", details),
    )
    conn.commit()
    cur.close()


def resources_get_audit_log(resource_id, limit=10):
    conn = get_connection()
    return pd.read_sql(
        "SELECT action, changed_by, changed_at, details FROM public_resources_audit_log "
        "WHERE resource_id = %s ORDER BY changed_at DESC LIMIT %s",
        conn, params=(int(resource_id), limit),
    )




def resources_toggle_favorite(user_id, resource_id):
    conn = get_connection()
    cur = conn.cursor()
    # Check if exists
    cur.execute("SELECT 1 FROM public_resource_favorites WHERE user_id = %s AND resource_id = %s", (int(user_id), int(resource_id)))
    exists = cur.fetchone()
    if exists:
        cur.execute("DELETE FROM public_resource_favorites WHERE user_id = %s AND resource_id = %s", (int(user_id), int(resource_id)))
        is_fav = False
    else:
        cur.execute("INSERT INTO public_resource_favorites (user_id, resource_id) VALUES (%s, %s)", (int(user_id), int(resource_id)))
        is_fav = True
    conn.commit()
    cur.close()
    return is_fav

def resources_get_favorites(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT resource_id FROM public_resource_favorites WHERE user_id = %s", (int(user_id),))
    favs = [r[0] for r in cur.fetchall()]
    cur.close()
    return favs

def resources_record_recent(user_id, resource_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO public_resource_recent (user_id, resource_id, viewed_at)
        VALUES (%s, %s, now())
        ON CONFLICT (user_id, resource_id, viewed_at) DO NOTHING
        """,
        (int(user_id), int(resource_id))
    )
    conn.commit()
    cur.close()

def resources_get_recent(user_id, limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT resource_id FROM public_resource_recent 
        WHERE user_id = %s 
        ORDER BY viewed_at DESC LIMIT %s
        """,
        (int(user_id), int(limit))
    )
    recents = []
    seen = set()
    for row in cur.fetchall():
        r_id = row[0]
        if r_id not in seen:
            seen.add(r_id)
            recents.append(r_id)
    cur.close()
    return recents

def resources_update_approval(resource_id, status, user_id, notes=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE public_resources SET approval_status = %s WHERE id = %s",
        (status, int(resource_id)),
    )
    # Log lifecycle event
    cur.execute(
        """
        INSERT INTO public_resource_lifecycle_events (resource_id, stage, actor_user_id, notes)
        VALUES (%s, %s, %s, %s)
        """,
        (int(resource_id), status, user_id, notes)
    )
    conn.commit()
    cur.close()
    resources_get_all.clear()
