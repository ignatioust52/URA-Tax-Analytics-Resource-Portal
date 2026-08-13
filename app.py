"""
URA Tax Dashboard — Streamlit application

Two top-level pages, chosen from the sidebar:
  - Dashboard: the analytics experience (KPIs, charts, raw data, chatbot)
  - Public Resources: browse/search for everyone; add/edit/delete for admins

SECURITY: all credentials are loaded from environment variables (.env),
never hardcoded. See .env.example for the template. .env itself is
excluded via .gitignore and must never be committed.

PERFORMANCE: every chart, KPI, and table on the Dashboard page queries
PostgreSQL directly with WHERE / GROUP BY / LIMIT clauses (SQL pushdown),
instead of loading the full invoice_tax_records table into pandas.

STRUCTURE: CSS lives in assets/style.css (loaded by load_css() below) rather
than inline in this file. Each Dashboard tab is its own render_*_tab()
function taking (where_sql, where_params, ...) so edits touch one small
function instead of one giant render_dashboard().
"""

import os
import base64
import secrets
import html as html_lib
from datetime import datetime
from datetime import datetime, timezone
import bcrypt
import email_utils

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from dotenv import load_dotenv
from fpdf import FPDF
import streamlit.components.v1 as components


load_dotenv()

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="URA Tax Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "URA-logo.png")
CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "style.css")

# ---------------------------------------------------------------------------
# URA BRAND COLORS — official palette (also mirrored as plain hex in
# assets/style.css, since CSS can't read Python variables)
# ---------------------------------------------------------------------------
URA_YELLOW = "#fff201"
URA_YELLOW_DARK = "#9e960e"
URA_BLUE = "#1755a6"
URA_BLUE_LIGHT = "#66a4d0"
URA_BLUE_PALE = "#c4d8e5"
URA_DARK = "#30302f"
URA_OLIVE = "#454104"
URA_GREEN = "#9ec470"

URA_BLUE_DARK = URA_DARK  # backwards-compatible alias
BG = "#F5F8FB"
GREY = "#5A6B87"

PALETTE = [URA_BLUE, URA_YELLOW, URA_BLUE_LIGHT, URA_YELLOW_DARK, URA_GREEN, URA_DARK]

# NOTE: The DEPARTMENTS Python list has been removed.
# Department names are now loaded live from the `departments` database table.
# Use departments_get_all() anywhere department options are needed.
# 'All' is still a valid resource-visibility sentinel value; it is NOT a real department row.

# Fixed color per tax category, so the same category is always the same
# color across every chart (pie, bar, sunburst) — not assigned by sort order.
CATEGORY_COLOR_MAP = {
    "VAT": URA_BLUE,
    "EXCISE": URA_YELLOW,
    "LOCAL_SERVICE": URA_BLUE_LIGHT,
    "WITHHOLDING": URA_OLIVE,
}

# How long a session survives with zero activity before being logged out.
# Checked passively on the next interaction — a fully idle tab with no
# clicks can't be proactively kicked out server-side by Streamlit.
SESSION_TIMEOUT_SECONDS = 1800


# ---------------------------------------------------------------------------
# STYLE / ASSET HELPERS
# ---------------------------------------------------------------------------
def load_css(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@st.cache_data
def get_logo_base64():
    if not os.path.exists(LOGO_PATH):
        return None
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_logo_html(width, extra_style=""):
    """Returns an <img> tag for the logo, or '' if no logo file exists."""
    logo_b64 = get_logo_base64()
    if not logo_b64:
        return ""
    return f'<img src="data:image/png;base64,{logo_b64}" width="{width}" style="{extra_style}">'


# Google Fonts — loaded as real <link> tags (more reliable than @import
# inside an f-string <style> block, which was silently getting overridden
# by Streamlit's own built-in font-face rules).
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700&family=Roboto:wght@400;500&family=Material+Symbols+Rounded" rel="stylesheet">
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<style>{load_css(CSS_PATH)}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------------------------
@st.cache_resource
def get_connection():
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        st.error(f"Missing database environment variables: {', '.join(missing)}. Check your .env file.")
        st.stop()
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = '180000';")  # 3 minutes
    return conn


def fmt_ugx(x):
    if x >= 1e12:
        return f"USh {x / 1e12:,.2f}T"
    if x >= 1e9:
        return f"USh {x / 1e9:,.2f}B"
    return f"USh {x:,.0f}"


FY_SQL_EXPR = """
    CASE
        WHEN EXTRACT(MONTH FROM effective_date) >= 7
        THEN EXTRACT(YEAR FROM effective_date)::TEXT || '/' || (EXTRACT(YEAR FROM effective_date)::INT + 1)::TEXT
        ELSE (EXTRACT(YEAR FROM effective_date)::INT - 1)::TEXT || '/' || EXTRACT(YEAR FROM effective_date)::TEXT
    END
"""


def build_where_clause(selected_fy, selected_categories, date_range, search_invoice):
    conditions = ["1=1"]
    params = []

    if selected_fy:
        fy_placeholders = ", ".join(["%s"] * len(selected_fy))
        conditions.append(f"({FY_SQL_EXPR}) IN ({fy_placeholders})")
        params.extend(selected_fy)

    if selected_categories:
        cat_placeholders = ", ".join(["%s"] * len(selected_categories))
        conditions.append(f"tax_category IN ({cat_placeholders})")
        params.extend(selected_categories)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        conditions.append("effective_date BETWEEN %s AND %s")
        params.extend([date_range[0], date_range[1]])

    if search_invoice and search_invoice.strip():
        conditions.append("invoice_id ILIKE %s")
        params.append(f"%{search_invoice.strip()}%")

    where_sql = " AND ".join(conditions)
    return where_sql, params


# ---------------------------------------------------------------------------
# DATA ACCESS — all SQL pushdown, cached 5 minutes
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def get_filter_options():
    conn = get_connection()
    fy_query = f"SELECT DISTINCT ({FY_SQL_EXPR}) AS fy FROM invoice_tax_records ORDER BY fy"
    fy_df = pd.read_sql(fy_query, conn)
    cat_df = pd.read_sql(
        "SELECT DISTINCT tax_category FROM invoice_tax_records ORDER BY tax_category", conn
    )
    range_df = pd.read_sql(
        "SELECT MIN(effective_date) AS min_d, MAX(effective_date) AS max_d FROM invoice_tax_records", conn
    )
    return (
        fy_df["fy"].tolist(),
        cat_df["tax_category"].tolist(),
        range_df["min_d"].iloc[0],
        range_df["max_d"].iloc[0],
    )


@st.cache_data(ttl=300)
def get_filtered_count(where_sql, where_params):
    conn = get_connection()
    query = f"SELECT COUNT(*) AS cnt FROM invoice_tax_records WHERE {where_sql}"
    return int(pd.read_sql(query, conn, params=where_params)["cnt"].iloc[0])


@st.cache_data(ttl=300)
def get_total_count():
    conn = get_connection()
    return int(pd.read_sql("SELECT COUNT(*) AS cnt FROM invoice_tax_records", conn)["cnt"].iloc[0])


@st.cache_data(ttl=300)
def get_kpi_totals(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT
            COALESCE(SUM(tax_amount), 0) AS total_tax,
            COALESCE(SUM(net_amount), 0) AS total_net,
            COUNT(*) AS total_records
        FROM invoice_tax_records
        WHERE {where_sql}
    """
    return pd.read_sql(query, conn, params=where_params).iloc[0]


@st.cache_data(ttl=300)
def get_top_category(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT tax_category, SUM(tax_amount) AS total
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY tax_category
        ORDER BY total DESC
        LIMIT 1
    """
    df = pd.read_sql(query, conn, params=where_params)
    return df.iloc[0] if not df.empty else None


@st.cache_data(ttl=300)
def get_category_summary(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT tax_category, SUM(tax_amount) AS tax_amount
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY tax_category
        ORDER BY tax_amount DESC
    """
    return pd.read_sql(query, conn, params=where_params)


@st.cache_data(ttl=300)
def get_fy_summary(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT ({FY_SQL_EXPR}) AS financial_year, SUM(tax_amount) AS tax_amount
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY financial_year
        ORDER BY financial_year
    """
    return pd.read_sql(query, conn, params=where_params)


@st.cache_data(ttl=300)
def get_rate_summary(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT tax_rate_name, SUM(tax_amount) AS tax_amount
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY tax_rate_name
        ORDER BY tax_amount ASC
    """
    return pd.read_sql(query, conn, params=where_params)


@st.cache_data(ttl=300)
def get_monthly_summary(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT DATE_TRUNC('month', effective_date) AS month_start, SUM(tax_amount) AS tax_amount
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY month_start
        ORDER BY month_start
    """
    return pd.read_sql(query, conn, params=where_params)


@st.cache_data(ttl=300)
def get_monthly_dict(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT TO_CHAR(DATE_TRUNC('month', effective_date), 'YYYY-MM') AS m, SUM(tax_amount) AS tax_amount
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY m
        ORDER BY m
    """
    df = pd.read_sql(query, conn, params=where_params)
    return df.set_index("m")["tax_amount"].round(2).to_dict()


@st.cache_data(ttl=300)
def get_sunburst_summary(where_sql, where_params):
    conn = get_connection()
    query = f"""
        SELECT ({FY_SQL_EXPR}) AS financial_year, tax_category, tax_rate_name, SUM(tax_amount) AS tax_amount
        FROM invoice_tax_records
        WHERE {where_sql}
        GROUP BY financial_year, tax_category, tax_rate_name
    """
    return pd.read_sql(query, conn, params=where_params)


@st.cache_data(ttl=300)
def get_sample_records(where_sql, where_params, limit=15):
    conn = get_connection()
    query = f"""
        SELECT invoice_id, tax_category, net_amount, tax_amount, effective_date
        FROM invoice_tax_records
        WHERE {where_sql}
        ORDER BY effective_date DESC
        LIMIT %s
    """
    return pd.read_sql(query, conn, params=where_params + [limit])


@st.cache_data(ttl=300)
def get_rate_options():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT DISTINCT tax_rate_name FROM invoice_tax_records WHERE tax_rate_name IS NOT NULL ORDER BY tax_rate_name",
        conn,
    )
    return df["tax_rate_name"].tolist()


@st.cache_data(ttl=300)
def get_net_bounds():
    conn = get_connection()
    df = pd.read_sql("SELECT MIN(net_amount) AS lo, MAX(net_amount) AS hi FROM invoice_tax_records", conn)
    return float(df["lo"].iloc[0]), float(df["hi"].iloc[0])


@st.cache_data(ttl=300)
def get_table_count(table_where, table_params):
    conn = get_connection()
    query = f"SELECT COUNT(*) AS cnt FROM invoice_tax_records WHERE {table_where}"
    return int(pd.read_sql(query, conn, params=table_params)["cnt"].iloc[0])


@st.cache_data(ttl=300)
def get_table_page(table_where, table_params, sort_col, ascending, offset, limit):
    conn = get_connection()
    direction = "ASC" if ascending else "DESC"
    query = f"""
        SELECT invoice_id, tax_category, tax_rate_name, net_amount, tax_amount, effective_date
        FROM invoice_tax_records
        WHERE {table_where}
        ORDER BY {sort_col} {direction}
        LIMIT %s OFFSET %s
    """
    return pd.read_sql(query, conn, params=table_params + [limit, offset])


# ---------------------------------------------------------------------------
# PDF REPORT
# ---------------------------------------------------------------------------
def build_pdf_report(total_tax, total_net, total_records, effective_rate, insight_text, filters_desc,
                      category_summary, fy_summary, sample):
    pdf = FPDF()
    pdf.add_page()

    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=8, w=22)

    pdf.set_xy(38, 10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(27, 79, 156)
    pdf.cell(0, 8, "URA Tax Invoice Dashboard - Report", ln=True)

    pdf.set_xy(38, 18)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 107, 135)
    pdf.cell(0, 6, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)

    pdf.ln(18)
    pdf.set_draw_color(255, 209, 0)
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 46, 99)
    pdf.cell(0, 7, "Applied Filters", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5.5, filters_desc)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 46, 99)
    pdf.cell(0, 7, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    metrics = [
        ("Total Tax Deducted", fmt_ugx(total_tax)),
        ("Total Net Amount", fmt_ugx(total_net)),
        ("Total Records", f"{total_records:,}"),
        ("Effective Tax Rate", f"{effective_rate:.1f}%"),
    ]
    for label, value in metrics:
        pdf.cell(70, 6.5, label, border=0)
        pdf.cell(0, 6.5, value, border=0, ln=True)
    pdf.ln(2)

    if insight_text:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_fill_color(255, 248, 222)
        pdf.set_text_color(13, 46, 99)
        pdf.multi_cell(0, 6, f"Insight: {insight_text}", fill=True)
        pdf.ln(2)

    def add_table(title, summary_df, label_col, value_col):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(13, 46, 99)
        pdf.cell(0, 7, title, ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(27, 79, 156)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 6.5, label_col.replace("_", " ").title(), border=1, fill=True)
        pdf.cell(0, 6.5, "Tax Deducted (UGX)", border=1, fill=True, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 30, 30)
        for _, r in summary_df.iterrows():
            pdf.cell(90, 6, str(r[label_col]), border=1)
            pdf.cell(0, 6, f"{float(r[value_col]):,.2f}", border=1, ln=True)
        pdf.ln(4)

    add_table("Tax Deducted by Category", category_summary, "tax_category", "tax_amount")
    add_table("Tax Deducted by Financial Year", fy_summary, "financial_year", "tax_amount")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(13, 46, 99)
    pdf.cell(0, 7, "Sample Records (most recent 15 of filtered selection)", ln=True)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(27, 79, 156)
    pdf.set_text_color(255, 255, 255)
    col_widths = [40, 35, 35, 35, 35]
    headers = ["Invoice ID", "Category", "Net Amount", "Tax Amount", "Effective Date"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 6.5, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(30, 30, 30)
    for _, row in sample.iterrows():
        pdf.cell(col_widths[0], 6, str(row["invoice_id"]), border=1)
        pdf.cell(col_widths[1], 6, str(row["tax_category"]), border=1)
        pdf.cell(col_widths[2], 6, f"{row['net_amount']:,.0f}", border=1)
        pdf.cell(col_widths[3], 6, f"{row['tax_amount']:,.0f}", border=1)
        pdf.cell(col_widths[4], 6, str(row["effective_date"]), border=1)
        pdf.ln()

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# APP USERS — Auth & Account Management
# ---------------------------------------------------------------------------
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
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM app_users WHERE email = %s", conn, params=(email.strip().lower(),))
    return df.iloc[0] if not df.empty else None


def create_user_session(user_id):
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_sessions (token, user_id, last_activity_at) VALUES (%s, %s, NOW())",
        (token, int(user_id)),
    )
    conn.commit()
    cur.close()
    return token


def get_active_session(token):
    """Returns the session+user row if the token is valid, active, and not
    timed out — otherwise deletes it (if present) and returns None."""
    if not token:
        return None
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT us.token, us.user_id, us.last_activity_at,
               u.email, u.role, u.department, u.status, u.is_active
        FROM user_sessions us
        JOIN app_users u ON u.id = us.user_id
        WHERE us.token = %s
        """,
        conn, params=(token,),
    )
    if df.empty:
        return None
    row = df.iloc[0]

    last_activity = row["last_activity_at"]
    if hasattr(last_activity, "to_pydatetime"):
        last_activity = last_activity.to_pydatetime()
    now = (
        datetime.now(timezone.utc)
        if getattr(last_activity, "tzinfo", None) is not None
        else datetime.now(timezone.utc).replace(tzinfo=None)
    )
    elapsed = (now - last_activity).total_seconds()

    if elapsed > SESSION_TIMEOUT_SECONDS or row["status"] != "active" or not bool(row["is_active"]):
        delete_user_session(token)
        return None
    return row


def touch_user_session(token):
    """Resets the idle clock — called on every authenticated interaction."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user_sessions SET last_activity_at = NOW() WHERE token = %s", (token,))
    conn.commit()
    cur.close()


def delete_user_session(token):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_sessions WHERE token = %s", (token,))
    conn.commit()
    cur.close()


def users_get_all():
    """Returns all non-pending users (active + disabled) ordered by id."""
    conn = get_connection()
    return pd.read_sql(
        "SELECT id, email, role, department, status, is_active, created_at FROM app_users "
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
            "SELECT id, email, requested_department, created_at FROM app_users "
            "WHERE status = 'pending' ORDER BY created_at",
            conn,
        )
    except Exception:
        return pd.DataFrame(columns=["id", "email", "requested_department", "created_at"])


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

def users_create(email, password_raw, role, dept_id_list, status="active"):
    """
    Admin-path account creation — bypasses the self-registration queue.
    dept_id_list : list of department IDs to grant access immediately.
    status       : 'active' for admin-created accounts (default).
    NOTE: is_active mirrors status throughout the app (redundant-but-safe;
    removing is_active would be a larger destructive migration).
    """
    hashed = bcrypt.hashpw(password_raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    cur = conn.cursor()
    is_active = (status == "active")
    cur.execute(
        """
        INSERT INTO app_users (email, password_hash, role, department, is_active, status)
        VALUES (%s, %s, %s, '', %s, %s)
        RETURNING id
        """,
        (email.strip().lower(), hashed, role if role else None, is_active, status),
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
            (email, password_hash, role, department, is_active, status, requested_department)
        VALUES (%s, %s, NULL, '', FALSE, 'pending', %s)
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
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE app_users SET status = 'active', is_active = TRUE, role = %s WHERE id = %s",
        (role, int(user_id)),
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
    cur.execute("SELECT role, is_active FROM app_users WHERE id = %s", (int(user_id),))
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        return False, "User account not found."

    target_role, target_active = user_row[0], user_row[1]

    if target_role == "admin" and target_active:
        cur.execute("SELECT COUNT(*) FROM app_users WHERE role = 'admin' AND is_active = TRUE")
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
    cur.execute("SELECT role, is_active FROM app_users WHERE id = %s", (int(user_id),))
    row = cur.fetchone()
    if not row:
        cur.close()
        return False, "User account not found."

    target_role, target_active = row[0], row[1]
    if target_role == "admin" and target_active:
        cur.execute("SELECT COUNT(*) FROM app_users WHERE role = 'admin' AND is_active = TRUE")
        active_admins = cur.fetchone()[0]
        if active_admins <= 1:
            cur.close()
            return False, "Cannot delete the only remaining active admin account."

    cur.execute("DELETE FROM app_users WHERE id = %s", (int(user_id),))
    conn.commit()
    cur.close()
    return True, "User account deleted."


def users_update_role_department(user_id, role, dept_id_list):
    """
    Updates a user's role and replaces their department access list.
    Blocks demoting the only remaining active admin away from 'admin'.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role, is_active FROM app_users WHERE id = %s", (int(user_id),))
    row = cur.fetchone()
    if not row:
        cur.close()
        return False, "User account not found."

    current_role, is_active_flag = row[0], row[1]
    if current_role == "admin" and is_active_flag and role != "admin":
        cur.execute("SELECT COUNT(*) FROM app_users WHERE role = 'admin' AND is_active = TRUE")
        active_admins = cur.fetchone()[0]
        if active_admins <= 1:
            cur.close()
            return False, "Cannot change role — this is the only remaining active admin."

    cur.execute("UPDATE app_users SET role = %s WHERE id = %s", (role, int(user_id)))
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


# ---------------------------------------------------------------------------
# PUBLIC RESOURCES — CRUD helpers
# ---------------------------------------------------------------------------
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
            last_viewed_at
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
        INSERT INTO public_resources (page_name, business_name, description, category, url, admin_only, department, added_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (page_name, business_name, description, category, url, admin_only, department, added_by),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    resource_department_access_set(new_id, dept_id_list)
    resources_log_audit(new_id, "create", added_by, f"Created '{business_name}'")
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


def resources_delete(resource_id, business_name, deleted_by):
    resources_log_audit(int(resource_id), "delete", deleted_by, f"Deleted '{business_name}'")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM public_resources WHERE id = %s", (int(resource_id),))
    conn.commit()
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


def humanize_dt(dt):
    if dt is None or pd.isna(dt):
        return "—"
    if hasattr(dt, "to_pydatetime"):
        dt = dt.to_pydatetime()

    if getattr(dt, "tzinfo", None) is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

    seconds = (now - dt).total_seconds()
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return "just now"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} min ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hr ago"
    days = hours / 24
    if days < 30:
        return f"{int(days)} day(s) ago"
    months = days / 30
    if months < 12:
        return f"{int(months)} month(s) ago"
    return f"{int(months / 12)} year(s) ago"

# ---------------------------------------------------------------------------
# DASHBOARD TABS — one function per tab
# ---------------------------------------------------------------------------
def render_trends_tab(where_sql, where_params):
    col_a, col_b = st.columns(2)

    fy_summary = get_fy_summary(where_sql, where_params)
    with col_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tax Deducted by Financial Year</div>', unsafe_allow_html=True)
        fig1 = px.bar(
            fy_summary, x="financial_year", y="tax_amount",
            labels={"tax_amount": "Total Tax Deducted (UGX)", "financial_year": "Financial Year"},
            color_discrete_sequence=[URA_BLUE],
        )
        fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10, l=10, r=10),
                            yaxis=dict(gridcolor="#EEF1F6"))
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    monthly = get_monthly_summary(where_sql, where_params)
    with col_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Monthly Tax Trend</div>', unsafe_allow_html=True)
        fig3 = px.line(
            monthly, x="month_start", y="tax_amount",
            labels={"tax_amount": "Total Tax Deducted (UGX)", "month_start": "Month"},
            markers=True, color_discrete_sequence=[URA_BLUE_DARK],
        )
        fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, b=10, l=10, r=10),
                            yaxis=dict(gridcolor="#EEF1F6"))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_breakdown_tab(where_sql, where_params):
    col_c, col_d = st.columns(2)

    category_summary = get_category_summary(where_sql, where_params)
    with col_c:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tax Deducted by Category</div>', unsafe_allow_html=True)
        fig2 = px.pie(category_summary, names="tax_category", values="tax_amount", hole=0.45,
                      color="tax_category", color_discrete_map=CATEGORY_COLOR_MAP)
        fig2.update_layout(paper_bgcolor="white", margin=dict(t=10, b=10, l=10, r=10),
                            legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    rate_summary = get_rate_summary(where_sql, where_params)
    with col_d:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tax Deducted by Rate Tier</div>', unsafe_allow_html=True)
        fig4 = px.bar(rate_summary, x="tax_amount", y="tax_rate_name", orientation="h",
                      labels={"tax_amount": "Total Tax Deducted (UGX)", "tax_rate_name": ""},
                      color="tax_rate_name", color_discrete_map=CATEGORY_COLOR_MAP)
        fig4.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(gridcolor="#EEF1F6"))
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_explore_tab(where_sql, where_params):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Interactive Breakdown — click a ring to zoom in</div>',
        unsafe_allow_html=True,
    )
    sunburst_df = get_sunburst_summary(where_sql, where_params)
    fig5 = px.sunburst(
        sunburst_df,
        path=["financial_year", "tax_category", "tax_rate_name"],
        values="tax_amount",
        color="tax_category",
        color_discrete_map=CATEGORY_COLOR_MAP,
    )
    fig5.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=550)
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("Click any segment to zoom into that Financial Year, Category, or Rate Tier.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_raw_data_tab(where_sql, where_params):
    st.markdown('<div class="section-title">Raw Data — Filter, Sort, Download</div>', unsafe_allow_html=True)

    rate_options_all = get_rate_options()
    net_lo, net_hi = get_net_bounds()

    with st.expander("Additional filters for this table", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            rt_selected = st.multiselect("Tax Rate Name", rate_options_all, default=rate_options_all, key="rt_filter")
        with fc2:
            net_range = st.slider("Net Amount range", min_value=net_lo, max_value=net_hi,
                                   value=(net_lo, net_hi), key="net_filter")
        with fc3:
            sort_col = st.selectbox(
                "Sort by",
                ["effective_date", "net_amount", "tax_amount", "invoice_id", "tax_category"],
                index=0,
            )
            sort_dir = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

    table_conditions = [where_sql, "tax_rate_name = ANY(%s)", "net_amount BETWEEN %s AND %s"]
    table_params = list(where_params) + [rt_selected, net_range[0], net_range[1]]
    table_where = " AND ".join(table_conditions)

    PAGE_SIZE = 200
    if "raw_data_page" not in st.session_state:
        st.session_state.raw_data_page = 0

    table_total = get_table_count(table_where, table_params)
    max_page = max((table_total - 1) // PAGE_SIZE, 0)
    st.session_state.raw_data_page = min(st.session_state.raw_data_page, max_page)

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("⬅️ Previous", disabled=st.session_state.raw_data_page == 0):
            st.session_state.raw_data_page -= 1
    with nav3:
        if st.button("Next ➡️", disabled=st.session_state.raw_data_page >= max_page):
            st.session_state.raw_data_page += 1
    with nav2:
        st.caption(
            f"Page {st.session_state.raw_data_page + 1} of {max_page + 1} "
            f"— {table_total:,} records match the table filters above."
        )

    offset = st.session_state.raw_data_page * PAGE_SIZE
    table_df = get_table_page(table_where, table_params, sort_col, sort_dir == "Ascending", offset, PAGE_SIZE)
    st.dataframe(table_df, use_container_width=True, height=420)

    st.caption(
        f"Showing {len(table_df):,} of {table_total:,} matching records "
        f"(download fetches this current page only, to keep exports fast)."
    )
    csv = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download this page as CSV",
        data=csv,
        file_name="ura_invoice_tax_filtered_page.csv",
        mime="text/csv",
    )


def render_ask_tab(where_sql, where_params, total_records, total_net, total_tax, effective_rate, is_admin):
    st.markdown('<div class="section-title">Ask the Data</div>', unsafe_allow_html=True)

    if not is_admin:
        st.info("This feature is available to administrators only.")
        return

    st.caption("Ask questions in plain language about the currently filtered data.")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.warning("No ANTHROPIC_API_KEY found. Add it to your .env file to enable this tab.")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    by_category = get_category_summary(where_sql, where_params).set_index("tax_category")["tax_amount"].round(2).to_dict()
    by_fy = get_fy_summary(where_sql, where_params).set_index("financial_year")["tax_amount"].round(2).to_dict()
    by_rate = get_rate_summary(where_sql, where_params).set_index("tax_rate_name")["tax_amount"].round(2).to_dict()
    by_month = get_monthly_dict(where_sql, where_params)

    data_context = f"""
You are answering questions about a URA invoice tax dataset, already filtered
to the user's current dashboard selection.

Totals for the CURRENT FILTERED SELECTION:
- Total records: {total_records}
- Total net amount (UGX): {total_net:,.2f}
- Total tax deducted (UGX): {total_tax:,.2f}
- Effective tax rate: {effective_rate:.2f}%

Tax deducted by category: {by_category}
Tax deducted by financial year: {by_fy}
Tax deducted by rate tier: {by_rate}
Tax deducted by month: {by_month}

Rules:
- Only answer using the numbers given above. Do not invent figures.
- Keep answers concise and business-relevant, in UGX with clear formatting.
""".strip()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_q = st.chat_input("e.g. Which category grew the most between financial years?")
    if user_q:
        st.session_state.chat_history.append(("user", user_q))
        with st.chat_message("user"):
            st.markdown(user_q)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=600,
                        system=data_context,
                        messages=[{"role": "user", "content": user_q}],
                    )
                    answer = "".join(
                        block.text for block in response.content if getattr(block, "type", "") == "text"
                    )
                except anthropic.APIError:
                    answer = (
                        "🤖💸 Uh oh — my brain ran out of credits before my mouth did. "
                        "Someone needs to top up in **Plans & Billing** on the Anthropic console."
                    )
                st.markdown(answer)
        st.session_state.chat_history.append(("assistant", answer))


# ---------------------------------------------------------------------------
# PAGE: DASHBOARD
# ---------------------------------------------------------------------------
def render_dashboard():
    is_admin = st.session_state.get("role") == "admin"

    header_logo_col, header_text_col = st.columns([1, 8])
    with header_logo_col:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=70)
    with header_text_col:
        st.markdown(
            """
            <div class="main-header">
                <h1>URA Tax Invoice Dashboard</h1>
                <p>Live data from PostgreSQL — a code-owned, interactive companion to the Power BI report</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.spinner("Connecting to PostgreSQL..."):
        get_connection()

    fy_options, category_options, min_date, max_date = get_filter_options()

    st.sidebar.markdown("## Filters")
    selected_fy = st.sidebar.multiselect("Financial Year", fy_options, default=[])
    selected_categories = st.sidebar.multiselect("Tax Category", category_options, default=[])
    date_range = st.sidebar.date_input(
        "Effective Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    search_invoice = st.sidebar.text_input(
        "Search Invoice ID", placeholder="e.g. INV-000123",
        help="Matches any part of the Invoice ID, case-insensitive",
    )

    search_active = bool(search_invoice and search_invoice.strip())
    where_sql, where_params = build_where_clause(selected_fy, selected_categories, date_range, search_invoice)

    if search_active:
        st.sidebar.caption(f"🔍 Filtering by Invoice ID containing \u201c{search_invoice.strip()}\u201d")

    if is_admin:
        if st.sidebar.button("🔄 Force Refresh Data Now"):
            st.cache_data.clear()
            st.success("Cache cleared — data will reload fresh.")
            st.rerun()

    filtered_count = get_filtered_count(where_sql, where_params)
    total_count = get_total_count()

    st.markdown(
        f'<p class="footnote">{filtered_count:,} of {total_count:,} records shown after filters.</p>',
        unsafe_allow_html=True,
    )

    kpi = get_kpi_totals(where_sql, where_params)
    total_tax = float(kpi["total_tax"])
    total_net = float(kpi["total_net"])
    total_records = int(kpi["total_records"])
    effective_rate = (total_tax / total_net * 100) if total_net else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tax Deducted", fmt_ugx(total_tax))
    with col2:
        st.metric("Total Net Amount", fmt_ugx(total_net))
    with col3:
        st.metric("Total Records", f"{total_records:,}")
    with col4:
        st.metric("Effective Tax Rate", f"{effective_rate:.1f}%")

    insight_text = ""
    top_cat = get_top_category(where_sql, where_params) if total_records else None
    if top_cat is not None:
        top_cat_share = (float(top_cat["total"]) / total_tax * 100) if total_tax else 0
        insight_text = (
            f"{top_cat['tax_category']} accounts for the largest share of tax deducted in the current selection "
            f"({top_cat_share:.1f}%)."
        )
        st.markdown(
            f'<div class="insight-box">💡 <b>{top_cat["tax_category"]}</b> accounts for the largest share of tax '
            f'deducted in the current selection ({top_cat_share:.1f}%).</div>',
            unsafe_allow_html=True,
        )

    filters_desc = (
        f"Financial Year: {', '.join(selected_fy) if selected_fy else 'All'} | "
        f"Tax Category: {', '.join(selected_categories) if selected_categories else 'All'} | "
        f"Date Range: {date_range[0]} to {date_range[1]}"
        if isinstance(date_range, tuple) and len(date_range) == 2
        else "All"
    )
    if search_active:
        filters_desc += f" | Invoice ID search: '{search_invoice.strip()}'"

    st.sidebar.markdown("---")
    if st.sidebar.button("📄 Generate PDF Report"):
        with st.spinner("Building PDF..."):
            cat_summary = get_category_summary(where_sql, where_params)
            fy_summary_df = get_fy_summary(where_sql, where_params)
            sample_df = get_sample_records(where_sql, where_params)
            pdf_bytes = build_pdf_report(
                total_tax, total_net, total_records, effective_rate, insight_text, filters_desc,
                cat_summary, fy_summary_df, sample_df,
            )
        st.sidebar.download_button(
            "⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"URA_Tax_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )

    tab_trends, tab_breakdown, tab_explore, tab_data, tab_ask = st.tabs(
        ["📈 Trends", "📊 Category Breakdown", "🧭 Explore", "📄 Raw Data", "🤖 Ask the Data"]
    )

    with tab_trends:
        render_trends_tab(where_sql, where_params)

    with tab_breakdown:
        render_breakdown_tab(where_sql, where_params)

    with tab_explore:
        render_explore_tab(where_sql, where_params)

    with tab_data:
        render_raw_data_tab(where_sql, where_params)

    with tab_ask:
        render_ask_tab(where_sql, where_params, total_records, total_net, total_tax, effective_rate, is_admin)


# ---------------------------------------------------------------------------
# PAGE: PUBLIC RESOURCES — browse/search for everyone; add/edit/delete for admins
# ---------------------------------------------------------------------------
def check_login():
    if st.session_state.get("authenticated", False):
        return True

    st.write("")  # small top spacing so the card isn't glued to the page edge
    col_spacer_l, col_form, col_spacer_r = st.columns([1, 3, 1])
    with col_form:
        left_col, right_col = st.columns([1, 1.2], gap="small")

        with left_col:
            logo_html_inner = render_logo_html(48)
            st.markdown(
                f"""
                <div class="auth-left-panel">
                    <div class="auth-logo-badge">{logo_html_inner}</div>
                    <div class="auth-left-title">URA Tax Dashboard</div>
                    <div class="auth-left-subtitle">
                        Secure access for URA staff — visualize, explore, and manage
                        tax invoice data in real time.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right_col:
            with st.container(key="auth-right-panel"):
                tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

            # ── Sign In ──────────────────────────────────────────────────
            with tab_signin:
                st.markdown('<div class="login-title">Welcome</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="login-subtitle">Please sign in with your account email and password</div>',
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    email_input = st.text_input(
                        "Email Address", value="", placeholder="e.g. user@ura.go.ug"
                    )
                    password_input = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Sign In", use_container_width=True)

                if submitted:
                    clean_email = email_input.strip().lower()
                    if not clean_email or not password_input:
                        st.error("Please enter both email and password.")
                    else:
                        user = user_get_by_email(clean_email)
                        if user is None:
                            st.error("Invalid email or password.")
                        else:
                            stored_hash = user["password_hash"]
                            user_status = str(user.get("status", "active"))
                            role = str(user["role"]) if user["role"] is not None else ""
                            dept = str(user["department"]) if user["department"] is not None else ""

                            if user_status == "pending":
                                st.warning(
                                    "⏳ Your account is awaiting administrator approval. "
                                    "You will be notified once it has been reviewed."
                                )
                            elif user_status == "disabled" or not bool(
                                user.get("is_active", True)
                            ):
                                st.error(
                                    "Account disabled. Please contact an administrator."
                                )
                            elif bcrypt.checkpw(
                                password_input.encode("utf-8"),
                                stored_hash.encode("utf-8"),
                            ):
                                st.session_state.authenticated = True
                                st.session_state.role = role
                                st.session_state.user_email = str(user["email"])
                                st.session_state.department = dept
                                st.session_state.user_id = int(user["id"])
                                # Load the multi-department access list for resource filtering
                                st.session_state.dept_access = user_department_access_get(
                                    int(user["id"])
                                )
                                _session_token = create_user_session(int(user["id"]))
                                st.query_params["session_token"] = _session_token
                                st.rerun()
                            else:
                                st.error("Invalid email or password.")

        # ── Create Account ────────────────────────────────────────────────
        with tab_register:
            with st.container(border=True):
                st.markdown('<div class="login-title">Create Account</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="login-subtitle">Request access — an administrator will '
                    'review and approve your account before you can sign in</div>',
                    unsafe_allow_html=True,
                )

                reg_email = st.text_input(
                    "Email Address",
                    placeholder="e.g. officer@ura.go.ug",
                    key="reg_email",
                )
                reg_password = st.text_input("Password", type="password", key="reg_password")
                reg_confirm = st.text_input(
                    "Confirm Password", type="password", key="reg_confirm"
                )

                try:
                    _reg_dept_df = departments_get_all()
                    _reg_dept_options = _reg_dept_df["name"].tolist() + [
                        "Other (please specify)"
                    ]
                except Exception:
                    _reg_dept_options = ["Other (please specify)"]

                reg_dept_select = st.selectbox(
                    "Department", options=_reg_dept_options, key="reg_dept_select"
                )

                reg_dept_other = ""
                if reg_dept_select == "Other (please specify)":
                    reg_dept_other = st.text_input(
                        "Please specify your department",
                        key="reg_dept_other",
                        placeholder="e.g. Research & Analytics",
                    )

                if st.button(
                    "Create Account",
                    use_container_width=True,
                    type="primary",
                    key="register_btn",
                ):
                    clean_email = reg_email.strip().lower()
                    _errors = []
                    if not clean_email:
                        _errors.append("Email is required.")
                    if not reg_password:
                        _errors.append("Password is required.")
                    elif reg_password != reg_confirm:
                        _errors.append("Passwords do not match.")
                    else:
                        _pw_ok, _pw_msg = is_password_strong(reg_password)
                        if not _pw_ok:
                            _errors.append(_pw_msg)

                    requested_dept = (
                        reg_dept_other.strip()
                        if reg_dept_select == "Other (please specify)"
                        else reg_dept_select
                    )
                    if not requested_dept:
                        _errors.append("Department is required.")

                    if _errors:
                        for _err in _errors:
                            st.error(_err)
                    else:
                        _existing = user_get_by_email(clean_email)
                        if _existing is not None:
                            st.error(
                                "An account with this email already exists. "
                                "Try signing in instead."
                            )
                        else:
                            try:
                                users_register(clean_email, reg_password, requested_dept)
                                email_utils.notify_registration_received(clean_email)
                                st.success(
                                    "✅ Your account has been created and is pending "
                                    "administrator approval. You will be able to sign in "
                                    "once an admin reviews your request."
                                )
                            except Exception as _e:
                                st.error(f"Failed to create account: {_e}")

        return False


def render_user_management():
    is_admin = st.session_state.get("role") == "admin"
    if not is_admin:
        st.warning("Access restricted to administrators.")
        return

    st.markdown('<div class="section-title">Admin User Management</div>', unsafe_allow_html=True)

    tab_pending, tab_active, tab_create = st.tabs(
        ["⏳ Pending Approvals", "👤 Active Users", "➕ Create Account"]
    )

    # ── TAB 1: Pending Approvals ─────────────────────────────────────────
    with tab_pending:
        pending_df = users_get_pending()

        if pending_df.empty:
            st.info("No pending registration requests at this time.")
        else:
            st.markdown(
                f'<div class="insight-box">💡 <b>{len(pending_df)}</b> account(s) awaiting your approval.</div>',
                unsafe_allow_html=True,
            )

            for _, puser in pending_df.iterrows():
                uid = int(puser["id"])
                requested = str(puser.get("requested_department") or "")

                with st.container(border=True):
                    st.markdown(f"**{puser['email']}**")
                    st.caption(
                        f"Requested department: **{requested or '—'}**  •  "
                        f"Signed up: {humanize_dt(puser['created_at'])}"
                    )

                    chosen_role = st.selectbox(
                        "Assign role",
                        options=["viewer", "admin"],
                        key=f"role_select_{uid}",
                    )

                    # Inline new-department form (outside st.form so the checkbox
                    # list updates immediately on rerun after creation)
                    st.markdown("**Grant department access:**")
                    _add_col, _btn_col = st.columns([4, 1])
                    with _add_col:
                        new_dept_name = st.text_input(
                            "New department name",
                            key=f"new_dept_{uid}",
                            placeholder="e.g. Research & Analytics",
                            label_visibility="collapsed",
                        )
                    with _btn_col:
                        if st.button("＋ Add", key=f"add_dept_btn_{uid}"):
                            if new_dept_name.strip():
                                try:
                                    departments_create(new_dept_name.strip())
                                    st.success(f"Added dept: {new_dept_name.strip()}")
                                    st.rerun()
                                except Exception as _e:
                                    st.error(f"Error adding department: {_e}")
                            else:
                                st.warning("Enter a department name first.")

                    # Department access checkboxes — 3-column grid, pre-tick if name matches request
                    dept_df_cur = departments_get_all()
                    selected_depts = []
                    _dept_rows = dept_df_cur.to_dict("records")
                    _chk_cols = st.columns(3)
                    for _i, _drow in enumerate(_dept_rows):
                        _pre = _drow["name"].lower() == requested.lower()
                        with _chk_cols[_i % 3]:
                            if st.checkbox(
                                _drow["name"],
                                value=_pre,
                                key=f"dept_{uid}_{_drow['id']}",
                            ):
                                selected_depts.append(int(_drow["id"]))

                    _btn_approve, _btn_reject = st.columns(2)
                    with _btn_approve:
                        if st.button(
                            "✅ Approve",
                            key=f"approve_{uid}",
                            use_container_width=True,
                            type="primary",
                        ):
                            users_approve(uid, chosen_role, selected_depts)
                            _dept_names = [d["name"] for d in _dept_rows if d["id"] in selected_depts]
                            email_utils.notify_account_approved(puser["email"], chosen_role, _dept_names)
                            st.success(
                                f"Approved **{puser['email']}** as {chosen_role}. "
                                f"{len(selected_depts)} department(s) granted."
                            )
                            st.rerun()
                    with _btn_reject:
                        if st.button(
                            "❌ Reject",
                            key=f"reject_{uid}",
                            use_container_width=True,
                        ):
                            # Rejecting a pending user is always safe — they have no role yet,
                            # so no admin-lockout risk. Row is kept as 'disabled' for audit trail.
                            users_reject(uid)
                            email_utils.notify_account_rejected(puser["email"])
                            st.warning(
                                f"Rejected **{puser['email']}**. "
                                "Account kept as disabled for audit trail — you can re-enable later."
                            )
                            st.rerun()

    # ── TAB 2: Active Users ──────────────────────────────────────────────
    with tab_active:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title" style="border-bottom: 1px solid #E3E8EF; '
            'padding-bottom: 0.4rem; font-size: 1rem; margin-bottom: 0.8rem;">'
            "Existing User Accounts</div>",
            unsafe_allow_html=True,
        )
        users_df = users_get_all()

        user_search = st.text_input(
            "Search by email",
            key="user_search_box",
            placeholder="Start typing an email address...",
        )
        if user_search and user_search.strip():
            _term = user_search.strip().lower()
            users_df = users_df[users_df["email"].str.lower().str.contains(_term, na=False)]

        if users_df.empty:
            st.info("No matching user accounts found." if user_search else "No user accounts found.")
        else:
            disp_df = users_df.copy()
            disp_df["created_at"] = disp_df["created_at"].apply(humanize_dt)
            disp_df["status"] = disp_df["status"].str.capitalize()
            # Show all granted departments (multi-value) instead of legacy single-column
            disp_df["departments"] = disp_df["id"].apply(
                lambda _uid: ", ".join(user_department_access_get(_uid)) or "—"
            )
            disp_df = disp_df[["id", "email", "role", "departments", "status", "created_at"]]
            disp_df.columns = ["ID", "Email", "Role", "Departments", "Status", "Created"]
            st.dataframe(disp_df, use_container_width=True, height=280)

            st.markdown("---")
            st.markdown("##### Manage User Account")
            user_options = {
                f"{r['email']} ({r['role'] or 'no role'}) — {str(r['status']).capitalize()}": r["id"]
                for _, r in users_df.iterrows()
            }
            selected_user_label = st.selectbox(
                "Select a user account to manage",
                options=list(user_options.keys()),
                key="manage_user_select",
            )
            managed_uid = user_options[selected_user_label]
            managed_user_row = users_df[users_df["id"] == managed_uid].iloc[0]

            _tab_toggle, _tab_role, _tab_pwd, _tab_delete = st.tabs(
                ["🔄 Toggle Status", "✏️ Role & Departments", "🔑 Reset Password", "🗑️ Delete"]
            )

            with _tab_toggle:
                if st.button("Toggle Active / Disabled Status", use_container_width=True, key="btn_toggle"):
                    success, msg = users_toggle_active(managed_uid)
                    if success:
                        _row_after = users_get_all()
                        _row_after = _row_after[_row_after["id"] == managed_uid].iloc[0]
                        email_utils.notify_account_status_changed(
                            managed_user_row["email"], bool(_row_after["is_active"])
                        )
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with _tab_role:
                _current_role = managed_user_row["role"] or "viewer"
                _role_options = ["viewer", "admin"]
                _role_idx = _role_options.index(_current_role) if _current_role in _role_options else 0
                new_role_edit = st.selectbox("Role", options=_role_options, index=_role_idx, key="role_edit_select")

                _current_user_depts = user_department_access_get(managed_uid)
                _dept_df_manage = departments_get_all()
                _manage_dept_ids = []
                if not _dept_df_manage.empty:
                    _manage_cols = st.columns(2)
                    for _i, _drow in enumerate(_dept_df_manage.to_dict("records")):
                        _pre = _drow["name"] in _current_user_depts
                        with _manage_cols[_i % 2]:
                            if st.checkbox(_drow["name"], value=_pre, key=f"manage_dept_{managed_uid}_{_drow['id']}"):
                                _manage_dept_ids.append(int(_drow["id"]))
                else:
                    st.info("No departments configured yet.")

                if st.button("Save Role & Departments", use_container_width=True, key="btn_role_save"):
                    success, msg = users_update_role_department(managed_uid, new_role_edit, _manage_dept_ids)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with _tab_pwd:
                new_pwd = st.text_input("New password", type="password", key="reset_pwd_input")
                if st.button("Reset Password", use_container_width=True, key="btn_pwd_reset"):
                    if new_pwd and new_pwd.strip():
                        success, msg = users_reset_password(managed_uid, new_pwd.strip())
                        if success:
                            email_utils.notify_password_reset(managed_user_row["email"], new_pwd.strip())
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Enter a new password first.")

            with _tab_delete:
                st.warning(f"This permanently deletes **{managed_user_row['email']}**. This cannot be undone.")
                confirm_delete = st.checkbox("I understand this is permanent", key="confirm_delete_chk")
                if st.button("🗑️ Delete Account Permanently", use_container_width=True, key="btn_delete", disabled=not confirm_delete):
                    success, msg = users_delete(managed_uid)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 3: Create Account ─────────────────────────────────────────────
    with tab_create:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title" style="border-bottom: 1px solid #E3E8EF; '
            'padding-bottom: 0.4rem; font-size: 1rem; margin-bottom: 0.8rem;">'
            "Create New User Account</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Admin bypass — account is created as active immediately, "
            "skipping the self-registration approval queue."
        )

        # Load departments before entering the form so we can render checkboxes inside it.
        # Their values are read correctly on the submit rerun (standard Streamlit forms behaviour).
        _dept_df_create = departments_get_all()
        _create_dept_ids = []

        # "+Add" lives OUTSIDE the form — Streamlit forms only allow st.form_submit_button
        # as a clickable trigger, so a plain st.button (needed here for an immediate rerun
        # after creating a department) can't sit inside st.form.
        st.markdown("**Add, rename, or delete departments:**")
        _add_col, _btn_col = st.columns([4, 1])
        with _add_col:
            new_dept_name_create = st.text_input(
                "New department name",
                key="new_dept_create",
                placeholder="e.g. Research & Analytics",
                label_visibility="collapsed",
            )
        with _btn_col:
            if st.button("＋ Add", key="add_dept_btn_create"):
                if new_dept_name_create.strip():
                    try:
                        departments_create(new_dept_name_create.strip())
                        st.success(f"Added dept: {new_dept_name_create.strip()}")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Error adding department: {_e}")
                else:
                    st.warning("Enter a department name first.")

        _existing_depts_df = departments_get_all()
        if not _existing_depts_df.empty:
            with st.expander(f"Manage existing departments ({len(_existing_depts_df)})"):
                for _erow in _existing_depts_df.to_dict("records"):
                    _dept_id_e = _erow["id"]
                    _rn_col, _save_col, _del_col = st.columns([3, 1, 1])
                    with _rn_col:
                        _renamed = st.text_input(
                            f"dept_{_dept_id_e}",
                            value=_erow["name"],
                            key=f"rename_dept_{_dept_id_e}",
                            label_visibility="collapsed",
                        )
                    with _save_col:
                        if st.button("💾 Save", key=f"save_dept_{_dept_id_e}", use_container_width=True):
                            if _renamed.strip() and _renamed.strip() != _erow["name"]:
                                success, msg = departments_update(_dept_id_e, _renamed.strip())
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with _del_col:
                        if st.button("🗑️ Delete", key=f"delete_dept_{_dept_id_e}", use_container_width=True):
                            success, msg = departments_delete(_dept_id_e)
                            if success:
                                st.success(f"Deleted '{_erow['name']}'.")
                                st.rerun()
                            else:
                                st.error(msg)

        with st.form("create_user_form", clear_on_submit=True):
            new_email = st.text_input("User Email", placeholder="e.g. officer@ura.go.ug")
            new_password = st.text_input("Temporary Password", type="password")
            new_role = st.selectbox("Role", options=["viewer", "admin"])

            st.markdown("**Department Access** (select all that apply):")
            if not _dept_df_create.empty:
                _form_cols = st.columns(2)
                for _i, _drow in enumerate(_dept_df_create.to_dict("records")):
                    with _form_cols[_i % 2]:
                        if st.checkbox(_drow["name"], key=f"create_dept_{_drow['id']}"):
                            _create_dept_ids.append(int(_drow["id"]))
            else:
                st.info(
                    "No departments configured yet. Add departments via the Pending Approvals tab."
                )

            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                clean_email = new_email.strip().lower()
                if not clean_email or not new_password:
                    st.error("Email and password are required.")
                else:
                    _pw_ok, _pw_msg = is_password_strong(new_password)
                    if not _pw_ok:
                        st.error(_pw_msg)
                    else:
                        try:
                            users_create(clean_email, new_password, new_role, _create_dept_ids)
                            _dept_names = [d["name"] for d in _dept_df_create.to_dict("records") if d["id"] in _create_dept_ids]
                            email_utils.notify_account_created_by_admin(
                                clean_email, new_password, new_role, _dept_names
                            )
                            st.success(f"Created account for '{clean_email}'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to create user: {e}")
        st.markdown("</div>", unsafe_allow_html=True)


def get_visible_resources(all_resources_df):
    """Shared visibility rule: admins see everything; everyone else sees
    non-admin_only resources whose department is either 'All' (no specific
    rows) or overlaps their granted dept_access. Same rule Public Resources
    already applies — factored out here so both pages can never disagree."""
    is_admin = st.session_state.get("role") == "admin"
    if is_admin or all_resources_df.empty:
        return all_resources_df

    user_dept_access = set(st.session_state.get("dept_access", []))
    has_admin_col = "admin_only" in all_resources_df.columns
    resource_dept_map = resources_get_department_map()

    def _resource_visible(res_row):
        if has_admin_col and res_row.get("admin_only"):
            return False
        specific_depts = resource_dept_map.get(int(res_row["id"]), [])
        if not specific_depts:
            return True
        return bool(user_dept_access.intersection(specific_depts))

    mask = all_resources_df.apply(_resource_visible, axis=1)
    return all_resources_df[mask].reset_index(drop=True)


def render_powerbi_reports():
    """Grouped nav bar built entirely from public_resources rows — no
    hardcoded pages or categories. Adding/editing/removing a report page
    is done through the same 'Add New Resource' form Public Resources
    already uses; any category name the admin types becomes its own
    nav group automatically."""
    import json

    st.markdown('<div class="section-title">Power BI Reports</div>', unsafe_allow_html=True)

    all_resources_df = resources_get_all()
    visible_df = get_visible_resources(all_resources_df)

    if visible_df.empty:
        st.info("No resources are visible to you yet. Ask an admin to add some via 'Manage Resources'.")
        return

    nav = []
    for cat in sorted(visible_df["category"].dropna().unique()):
        rows = visible_df[visible_df["category"] == cat].sort_values("id").to_dict("records")
        if not rows:
            continue
        if len(rows) == 1:
            nav.append({"label": rows[0]["page_name"], "url": rows[0]["url"]})
        else:
            nav.append({"label": cat, "pages": [{"label": r["page_name"], "url": r["url"]} for r in rows]})

    if not nav:
        st.info("No resources found.")
        return

    nav_json = json.dumps(nav)

    widget_html = f"""
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin:0; font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif; }}
      .navbar {{ display:flex; align-items:center; gap:6px; padding:8px 4px; flex-wrap:wrap; }}
      .nav-group {{ position:relative; }}
      .nav-btn {{ padding:8px 14px; background:{URA_BLUE_PALE}; color:{URA_BLUE};
                  border:none; border-radius:6px; font-size:13px; font-weight:600;
                  cursor:pointer; white-space:nowrap; }}
      .nav-btn:hover {{ background:{URA_BLUE_LIGHT}; color:#fff; }}
      .nav-btn.active {{ background:{URA_BLUE}; color:#fff; }}
      .dropdown {{ display:none; position:absolute; top:105%; left:0; background:#fff;
                   border:1px solid #e2e6ec; border-radius:8px;
                   box-shadow:0 8px 24px rgba(0,0,0,0.12); min-width:240px;
                   padding:6px; z-index:20; }}
      .nav-group:hover .dropdown, .nav-group:focus-within .dropdown {{ display:block; }}
      .dropdown button {{ display:block; width:100%; text-align:left; padding:8px 10px;
                          background:none; border:none; border-radius:6px; font-size:12.5px;
                          color:{URA_DARK}; cursor:pointer; }}
      .dropdown button:hover {{ background:{URA_BLUE_PALE}; }}
      .dropdown button.active {{ background:{URA_BLUE}; color:#fff; }}
      iframe.report {{ width:100%; height:640px; border:none; border-radius:10px;
                       background:#fff; margin-top:10px; }}
    </style>
    <div class="navbar" id="navbar"></div>
    <iframe class="report" id="reportFrame" allowFullScreen></iframe>
    <script>
      const NAV = {nav_json};
      const navbar = document.getElementById("navbar");
      const frame = document.getElementById("reportFrame");

      function goToPage(url, btnEl) {{
        document.querySelectorAll(".nav-btn, .dropdown button")
          .forEach(b => b.classList.remove("active"));
        if (btnEl) btnEl.classList.add("active");
        frame.src = url;
      }}

      NAV.forEach((item, idx) => {{
        if (item.pages) {{
          const group = document.createElement("div");
          group.className = "nav-group";
          group.tabIndex = 0;
          const btn = document.createElement("button");
          btn.className = "nav-btn";
          btn.textContent = item.label;
          group.appendChild(btn);
          const dropdown = document.createElement("div");
          dropdown.className = "dropdown";
          item.pages.forEach(sub => {{
            const subBtn = document.createElement("button");
            subBtn.textContent = sub.label;
            subBtn.onclick = () => goToPage(sub.url, subBtn);
            dropdown.appendChild(subBtn);
          }});
          group.appendChild(dropdown);
          btn.onclick = () => goToPage(item.pages[0].url, btn);
          navbar.appendChild(group);
        }} else {{
          const btn = document.createElement("button");
          btn.className = "nav-btn";
          btn.textContent = item.label;
          btn.onclick = () => goToPage(item.url, btn);
          navbar.appendChild(btn);
        }}
        if (idx === 0) {{
          const firstUrl = item.url || (item.pages && item.pages[0].url);
          frame.src = firstUrl;
        }}
      }});
    </script>
    """
    components.html(widget_html, height=700, scrolling=False)

def render_public_resources():
    is_admin = st.session_state.get("role") == "admin"
    all_resources_df = resources_get_all()

    # Viewers see resources where admin_only is False AND the resource's department is either
    # 'All' (visible to everyone) OR is in the viewer's granted user_department_access list.
    # dept_access is a list of department names loaded from user_department_access at login time.
    if not is_admin:
        user_dept_access = set(st.session_state.get("dept_access", []))
        if not all_resources_df.empty:
            has_admin_col = "admin_only" in all_resources_df.columns
            resource_dept_map = resources_get_department_map()

            def _resource_visible(res_row):
                if has_admin_col and res_row.get("admin_only"):
                    return False
                specific_depts = resource_dept_map.get(int(res_row["id"]), [])
                if not specific_depts:
                    return True  # no specific rows = visible to everyone
                return bool(user_dept_access.intersection(specific_depts))

            mask = all_resources_df.apply(_resource_visible, axis=1)
            resources_df = all_resources_df[mask].reset_index(drop=True)
        else:
            resources_df = all_resources_df
    else:
        resources_df = all_resources_df

    if "resource_view" not in st.session_state:
        st.session_state.resource_view = "browse"
    if "editing_resource_id" not in st.session_state:
        st.session_state.editing_resource_id = None

    # MAIN AREA — default browse / search / view page
    # Search / category / resource picker are rendered in the top_nav_strip container.
    # Read their values from session_state to avoid duplicate Streamlit widgets.
    if resources_df.empty:
        st.info("No resources match your visibility permissions or filters.")
        return

    search_term = st.session_state.get("pr_search_term", "")
    selected_categories = st.session_state.get("pr_selected_categories", [])
    selected_name = st.session_state.get("pr_resource_select")

    display_df = resources_df
    if search_term and search_term.strip():
        term = search_term.strip().lower()
        mask = (
            display_df["page_name"].str.lower().str.contains(term, na=False)
            | display_df["business_name"].str.lower().str.contains(term, na=False)
            | display_df["category"].fillna("").str.lower().str.contains(term, na=False)
        )
        display_df = display_df[mask]

    if selected_categories:
        display_df = display_df[display_df["category"].isin(selected_categories)]

    if display_df.empty:
        st.warning("No resources match your search.")
        return

    # Ensure selected_name falls back to first available if missing or invalid
    available_names = list(display_df["business_name"])
    if not selected_name or selected_name not in available_names:
        selected_name = available_names[0]
        st.session_state["pr_resource_select"] = selected_name
    # MAIN AREA — "Add New Resource" page
    if is_admin and st.session_state.resource_view == "add":
        if st.button("⬅️ Back to Resources"):
            st.session_state.resource_view = "browse"
            st.rerun()

        st.markdown('<div class="section-title">Add New Resource</div>', unsafe_allow_html=True)

        # A live, non-form URL field just for testing — fields inside st.form don't
        # update their Python value until the form is submitted, so a Test Link
        # button placed outside the form can't read a URL typed inside it.
        test_url_input = st.text_input(
            "Test a URL before adding (optional)",
            key="test_url_field",
            placeholder="Paste a URL here to test it, then copy it into the form below",
        )
        if st.button("🔗 Test Link", key="test_link_add"):
            if test_url_input and test_url_input.strip():
                with st.spinner("Testing resource URL..."):
                    ok, msg = test_resource_url(test_url_input.strip())
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.warning("Paste a URL above first, then click Test Link.")

        with st.form("add_resource_form", clear_on_submit=True):
            new_page = st.text_input("Page Name")
            new_business = st.text_input("Business / Organization Name")
            new_description = st.text_area("Description")
            new_category = st.text_input("Category (e.g. Government, URA, Partner)")
            new_url = st.text_input("URL (e.g. Power BI embed link, website, etc.)")
            st.markdown("**Department Visibility:**")
            new_visible_all = st.checkbox("Visible to everyone (All)", value=True, key="new_res_all")
            _dept_df_add = departments_get_all()
            new_dept_ids = []
            if not _dept_df_add.empty:
                _add_cols = st.columns(2)
                for _i, _drow in enumerate(_dept_df_add.to_dict("records")):
                    with _add_cols[_i % 2]:
                        if st.checkbox(_drow["name"], key=f"add_dept_{_drow['id']}"):
                            new_dept_ids.append(int(_drow["id"]))
            new_admin_only = st.checkbox("Admin only", value=False)
            submitted = st.form_submit_button("Add Resource")

            if submitted:
                if not new_page or not new_business or not new_url:
                    st.error("Page Name, Business Name, and URL are required.")
                elif not new_visible_all and not new_dept_ids:
                    st.error("Select at least one department, or check 'Visible to everyone'.")
                else:
                    current_user = st.session_state.get("user_email", "admin@ura.go.ug")
                    dept_ids_to_save = [] if new_visible_all else new_dept_ids
                    resources_create(new_page, new_business, new_description, new_category, new_url, new_admin_only, dept_ids_to_save, current_user)
                    st.success(f"Added '{new_business}'.")
                    st.cache_data.clear()
                    st.session_state.resource_view = "browse"
                    st.rerun()

        
        return

    # MAIN AREA — "Edit Resource" page
    if is_admin and st.session_state.resource_view == "edit":
        if st.button("⬅️ Back to Resources"):
            st.session_state.resource_view = "browse"
            st.session_state.editing_resource_id = None
            st.rerun()

        row = all_resources_df[all_resources_df["id"] == st.session_state.editing_resource_id]
        if row.empty:
            st.warning("This resource no longer exists.")
            st.session_state.resource_view = "browse"
            st.rerun()
        row = row.iloc[0]

        st.markdown(f'<div class="section-title">Edit — {html_lib.escape(str(row["business_name"]))}</div>', unsafe_allow_html=True)
        with st.form("edit_resource_form"):
            edit_page = st.text_input("Page Name", value=row["page_name"])
            edit_business = st.text_input("Business Name", value=row["business_name"])
            edit_description = st.text_area("Description", value=row["description"] or "")
            edit_category = st.text_input("Category", value=row["category"] or "")
            edit_url = st.text_input("URL", value=row["url"])
            _current_res_depts = resource_department_access_get(int(row["id"]))
            st.markdown("**Department Visibility:**")
            edit_visible_all = st.checkbox("Visible to everyone (All)", value=(len(_current_res_depts) == 0), key="edit_res_all")
            _dept_df_edit = departments_get_all()
            edit_dept_ids = []
            if not _dept_df_edit.empty:
                _edit_cols = st.columns(2)
                for _i, _drow in enumerate(_dept_df_edit.to_dict("records")):
                    _pre = _drow["name"] in _current_res_depts
                    with _edit_cols[_i % 2]:
                        if st.checkbox(_drow["name"], value=_pre, key=f"edit_dept_{row['id']}_{_drow['id']}"):
                            edit_dept_ids.append(int(_drow["id"]))
            edit_admin_only = st.checkbox("Admin only", value=bool(row.get("admin_only", False)))

            col_save, col_delete = st.columns(2)
            with col_save:
                save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True)
            with col_delete:
                delete_clicked = st.form_submit_button("🗑️ Delete", use_container_width=True)

            if save_clicked:
                if not edit_visible_all and not edit_dept_ids:
                    st.error("Select at least one department, or check 'Visible to everyone'.")
                else:
                    current_user = st.session_state.get("user_email", "admin@ura.go.ug")
                    dept_ids_to_save = [] if edit_visible_all else edit_dept_ids
                    resources_update(int(row["id"]), edit_page, edit_business, edit_description, edit_category, edit_url, edit_admin_only, dept_ids_to_save, current_user)
                    st.success("Updated.")
                    st.cache_data.clear()
                    st.session_state.resource_view = "browse"
                    st.rerun()

            if delete_clicked:
                current_user = st.session_state.get("user_email", "admin@ura.go.ug")
                resources_delete(int(row["id"]), row["business_name"], current_user)
                st.warning(f"Deleted '{row['business_name']}'.")
                st.cache_data.clear()
                st.session_state.resource_view = "browse"
                st.rerun()

        # Streamlit forms cannot hold arbitrary interactive buttons, so Test Link lives outside
        if st.button("🔗 Test Link", use_container_width=False):
            with st.spinner("Testing resource URL..."):
                ok, msg = test_resource_url(row["url"])
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        return

        # MAIN AREA — default browse / search / view page (bottom duplicate removed)
        # Read search/category/resource values from session_state (top nav strip).
        if resources_df.empty:
            st.info("No resources match your visibility permissions or filters.")
            return

        search_term = st.session_state.get("pr_search_term", "")
        selected_categories = st.session_state.get("pr_selected_categories", [])
        selected_name = st.session_state.get("pr_resource_select")

    display_df = resources_df
    if search_term and search_term.strip():
        term = search_term.strip().lower()
        mask = (
            display_df["page_name"].str.lower().str.contains(term, na=False)
            | display_df["business_name"].str.lower().str.contains(term, na=False)
            | display_df["category"].fillna("").str.lower().str.contains(term, na=False)
        )
        display_df = display_df[mask]

    if selected_categories:
        display_df = display_df[display_df["category"].isin(selected_categories)]

    if display_df.empty:
        st.warning("No resources match your search.")
        return

    # Ensure selected_name falls back to first available if missing or invalid
    available_names = list(display_df["business_name"])
    if not selected_name or selected_name not in available_names:
        selected_name = available_names[0]
        st.session_state["pr_resource_select"] = selected_name
    selected_row = display_df[display_df["business_name"] == selected_name].iloc[0]
    resource_id = int(selected_row["id"])

    # Record view count once when selected resource changes
    if st.session_state.get("last_viewed_resource_id") != resource_id:
        resources_record_view(resource_id)
        st.session_state.last_viewed_resource_id = resource_id

    added_rel = humanize_dt(selected_row.get("created_at"))
    updated_rel = humanize_dt(selected_row.get("updated_at"))

    st.markdown(f"### {html_lib.escape(str(selected_row['business_name']))}")
    if selected_row.get("description"):
        st.markdown(html_lib.escape(str(selected_row['description'])))

    meta_parts = [f"🕒 Added {added_rel}", f"Updated {updated_rel}"]
    if selected_row.get("category"):
        meta_parts.append(f"🏷️ Category: {selected_row['category']}")
    _resource_depts = resource_department_access_get(resource_id)
    dept_label = ", ".join(_resource_depts) if _resource_depts else "All"
    meta_parts.append(f"🏢 Dept: {dept_label}")
    if is_admin and selected_row.get("admin_only"):
        meta_parts.append("🔒 Admin Only")
    st.caption(" • ".join(meta_parts))

    # Admin-only detail card: view counts, timestamps, user metadata, audit log
    if is_admin:
        with st.expander("👑 Admin Resource Stats & Audit Log", expanded=False):
            ac1, ac2, ac3, ac4 = st.columns(4)
            with ac1:
                st.metric("View Count", int(selected_row.get("view_count") or 0))
            with ac2:
                st.metric("Last Viewed", humanize_dt(selected_row.get("last_viewed_at")))
            with ac3:
                st.metric("Added By", selected_row.get("added_by") or "—")
            with ac4:
                st.metric("Last Edited By", selected_row.get("last_edited_by") or "—")

            st.markdown("##### Recent Audit Activity")
            audit_df = resources_get_audit_log(resource_id, limit=10)
            if not audit_df.empty:
                if "changed_at" in audit_df.columns:
                    audit_df["changed_at"] = audit_df["changed_at"].apply(humanize_dt)
                st.dataframe(audit_df, use_container_width=True)
            else:
                st.info("No audit log records for this resource yet.")

    components.iframe(selected_row["url"], height=600, scrolling=True)


# ---------------------------------------------------------------------------
# TOP-LEVEL NAVIGATION
# ---------------------------------------------------------------------------
# Attempt to restore an existing session from the URL before showing the
# login screen — this is what makes a browser refresh keep you logged in,
# and what enforces the inactivity timeout on the next interaction.
if not st.session_state.get("authenticated", False):
    _restore_token = st.query_params.get("session_token")
    _restored = get_active_session(_restore_token) if _restore_token else None
    if _restored is not None:
        st.session_state.authenticated = True
        st.session_state.role = str(_restored["role"]) if _restored["role"] is not None else ""
        st.session_state.user_email = str(_restored["email"])
        st.session_state.department = str(_restored["department"]) if _restored["department"] is not None else ""
        st.session_state.user_id = int(_restored["user_id"])
        st.session_state.dept_access = user_department_access_get(int(_restored["user_id"]))
        st.session_state.session_token = _restore_token
    elif _restore_token:
        # Token was present but invalid/expired — clear it so it doesn't linger in the URL
        del st.query_params["session_token"]

if not check_login():
    st.stop()

# Keep the idle-timeout clock alive on every authenticated interaction
if st.session_state.get("session_token"):
    touch_user_session(st.session_state["session_token"])

# ---------------------------------------------------------------------------
# TOP NAVIGATION — single blue header bar. Row 1 = brand + page tabs +
# user/logout. Row 2 (Public Resources only) = search/filter/resource-pick
# on the left, admin Add/Edit shortcuts on the right. Nothing here is new
# functionality — every control below is the exact same widget that used
# to live in st.sidebar or in the "Find a Resource" section, just re-homed.
# ---------------------------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Public Resources"

is_admin = st.session_state.get("role") == "admin"
nav_options = ["Public Resources"]
if is_admin:
    nav_options.append("User Management")

page = st.session_state.current_page

# Pulled up-front so row 2 of the nav bar can build its search/category/
# resource-picker widgets before render_public_resources() runs.
_all_resources_df = resources_get_all() if page == "Public Resources" else pd.DataFrame()
_visible_resources_df = (
    get_visible_resources(_all_resources_df) if page == "Public Resources" else pd.DataFrame()
)

with st.container(key="top_nav_strip"):
    # ---- Row 1: brand · page tabs · user info · logout ----
    _row1_widths = [2.6] + [(1.6 if opt == "Public Resources" else 1.7) for opt in nav_options] + [4.0, 3.0, 1.2]
    row1 = st.columns(_row1_widths)

    with row1[0]:
        logo_html_top = render_logo_html(30)
        st.markdown(
            f'<div class="top-nav-brand">{logo_html_top}'
            f'<span class="top-nav-brand-text">URA Resource Portal</span></div>',
            unsafe_allow_html=True,
        )

    for i, opt in enumerate(nav_options):
        with row1[1 + i]:
            _is_active = st.session_state.current_page == opt
            if st.button(
                opt,
                key=f"navbtn_{opt.replace(' ', '_')}",
                use_container_width=True,
                type="primary" if _is_active else "secondary",
            ):
                st.session_state.current_page = opt
                st.rerun()

    with row1[-2]:
        _dept_display = ", ".join(st.session_state.get("dept_access", [])) or "All"
        st.markdown(
            f'<div class="top-nav-user">{st.session_state.get("user_email", "User")}'
            f'<br><span class="top-nav-role">'
            f'{st.session_state.get("role", "").title()} • {_dept_display}</span></div>',
            unsafe_allow_html=True,
        )

    with row1[-1]:
        if st.button("Log out", key="top_logout_btn", use_container_width=True):
            if st.session_state.get("session_token"):
                delete_user_session(st.session_state["session_token"])
                del st.query_params["session_token"]
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.user_email = None
            st.session_state.department = None
            st.session_state.session_token = None
            st.session_state.resource_view = "browse"
            st.rerun()

    # ---- Row 2: Public Resources search/filter/pick + admin shortcuts ----
    if page == "Public Resources":
        st.markdown('<hr class="top-nav-divider">', unsafe_allow_html=True)
        browsing = st.session_state.get("resource_view", "browse") == "browse"

        if browsing:
            col_resources, col_management = st.columns([2, 1])

            with col_resources:
                with st.container(key="resources-card"):
                    st.markdown('<div class="ui-card-title">Resources View</div>', unsafe_allow_html=True)
                    search_col, cat_col, pick_col = st.columns(3)
                    with search_col:
                        st.text_input(
                            "Search by name, business, or category",
                            placeholder="e.g. VAT, URA, Website",
                            key="pr_search_term",
                        )
                    with cat_col:
                        _available_categories = (
                            sorted([str(c) for c in _visible_resources_df["category"].dropna().unique() if str(c).strip()])
                            if not _visible_resources_df.empty else []
                        )
                        st.multiselect("Filter by Category", options=_available_categories, key="pr_selected_categories")
                    with pick_col:
                        _pick_options = _visible_resources_df["business_name"].tolist() if not _visible_resources_df.empty else []
                        if _pick_options:
                            st.selectbox("Choose a resource to view", options=_pick_options, key="pr_resource_select")

            if is_admin:
                with col_management:
                    with st.container(key="management-card"):
                        st.markdown('<div class="ui-card-title">Management Actions</div>', unsafe_allow_html=True)
                        add_col, edit_col = st.columns(2)
                        with add_col:
                            if st.button("➕ Add New Resource", type="primary", use_container_width=True, key="nav_add_resource_btn"):
                                st.session_state.resource_view = "add"
                                st.rerun()
                        with edit_col:
                            _edit_options = _all_resources_df["business_name"].tolist() if not _all_resources_df.empty else []
                            if _edit_options and st.button("✏️ Edit Selected", use_container_width=True, key="nav_edit_resource_btn"):
                                _target_row = _all_resources_df[
                                    _all_resources_df["business_name"] == st.session_state.get("pr_resource_select")
                                ]
                                if not _target_row.empty:
                                    st.session_state.editing_resource_id = int(_target_row.iloc[0]["id"])
                                    st.session_state.resource_view = "edit"
                                    st.rerun()

        
if page == "Public Resources":
    render_public_resources()
elif page == "User Management":
    render_user_management()