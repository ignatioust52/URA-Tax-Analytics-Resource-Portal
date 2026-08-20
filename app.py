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

DESIGN: assets/style.css is the single source of truth for the URA visual
identity (navy #243F8D / gold #FFF200 / terracotta #B54834 institutional
theme, Fraunces + IBM Plex typography). Do not add another inline <style>
block here or in view files — extend style.css instead so every page
(Public Resources, User Management, Analytics, the login split-screen)
stays visually consistent.
"""

import os

import streamlit as st
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="URA Tax Dashboard",
    page_icon="assets/URA-logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "URA-logo.png")
CSS_PATH = os.path.join(os.path.dirname(__file__), "assets", "style.css")

from core.utils import render_logo_html
from core.db import get_connection

# ---------------------------------------------------------------------------
# STYLE / ASSET HELPERS
# ---------------------------------------------------------------------------
def load_css(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Google Fonts — Fraunces (display), IBM Plex Sans (body/UI), IBM Plex Mono
# (figures), plus Material Symbols Rounded (icons for the floating support
# bubbles in views/public_resources.py). These are the faces style.css
# assumes are loaded; if you change the type system, update both this link
# and the font-family rules in style.css together.
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Material+Symbols+Rounded&display=swap" rel="stylesheet">
    """,
    unsafe_allow_html=True,
)

# style.css is the only theme layer for this app — every page inherits it
# automatically. Nothing else should render a <style> block.
st.markdown(f"<style>{load_css(CSS_PATH)}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# APP USERS — Auth & Account Management
# ---------------------------------------------------------------------------

from core.db_departments import user_department_access_get
from core import db_users as db_users_module
from core import db_resources as db_resources_module
from core.db_resources import resources_get_all
from views.public_resources import render_public_resources, get_visible_resources
import views.public_resources as public_resources_view
from views.user_management import render_user_management
from views.analytics import render_analytics
from core.auth import (
    get_active_session,
    touch_user_session,
    delete_user_session,
    check_login,
)

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

if st.session_state.get("show_login", False) and not st.session_state.get("authenticated", False):
    if check_login():
        st.session_state.show_login = False
        st.rerun()
    else:
        st.stop()

# Keep the idle-timeout clock alive on every authenticated interaction
if st.session_state.get("session_token"):
    touch_user_session(st.session_state["session_token"])

# ---------------------------------------------------------------------------
# TOP NAVIGATION — single navy header bar, matching the mockup's topbar.
# Row 1 = brand + page tabs + user/logout. Row 2 (Public Resources only) =
# search/filter/resource-pick on the left, admin Add/Edit shortcuts on the
# right. Nothing here is new functionality — every control below is the
# exact same widget that used to live in st.sidebar or in the "Find a
# Resource" section, just re-homed.
# ---------------------------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Public Resources"

is_admin = st.session_state.get("role") == "admin"
nav_options = ["Public Resources"]
if is_admin:
    nav_options.append("User Management")
    nav_options.append("Analytics")
    nav_options.append("Governance")

page = st.session_state.current_page

# Pulled up-front so row 2 of the nav bar can build its search/category/
# resource-picker widgets before render_public_resources() runs.
_all_resources_df = resources_get_all() if page == "Public Resources" else pd.DataFrame()
_visible_resources_df = (
    get_visible_resources(_all_resources_df) if page == "Public Resources" else pd.DataFrame()
)

# ---------------------------------------------------------------------------
# TOP HEADER — single navy bar: brand + live-report status, styled by the
# .top-nav-brand / .ura-live-badge rules in style.css.
# ---------------------------------------------------------------------------
with st.container(key="top_nav_header"):
    head_col1, head_col2 = st.columns([3, 2])

    with head_col1:
        logo_html_top = render_logo_html(36)
        st.markdown(
            f'<div class="top-nav-brand">{logo_html_top}'
            f'<div class="top-nav-brand-text">'
            f'<span class="top-nav-main-title">Uganda Revenue Authority</span>'
            f'<span class="top-nav-subtitle">DEVELOPING UGANDA TOGETHER · REVENUE DASHBOARD</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    with head_col2:
        st.markdown(
            '<div style="display: flex; justify-content: flex-end; align-items: center; gap: 1rem; height: 100%;">'
            '<span class="ura-live-badge"><span class="ura-live-dot"></span> Live report</span>'
            '</div>',
            unsafe_allow_html=True,
        )

# Signature triband divider — the mockup's single most recognizable motif,
# used once here as the seam between the brand bar and the tab strip.
st.markdown('<div class="ura-stripe"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOP NAVIGATION STRIP (page tabs + user/logout, underline style)
# ---------------------------------------------------------------------------
with st.container(key="top_blue_navbar"):
    _nav_widths = [(1.8 if opt == "Public Resources" else 1.8) for opt in nav_options] + [4.0, 2.5, 1.4]
    nav_cols = st.columns(_nav_widths)

    for i, opt in enumerate(nav_options):
        with nav_cols[i]:
            _is_active = st.session_state.current_page == opt
            tab_label = opt
            if st.button(
                tab_label,
                key=f"navbtn_{opt.replace(' ', '_')}",
                use_container_width=True,
                type="primary" if _is_active else "secondary",
            ):
                st.session_state.current_page = opt
                st.rerun()

    with nav_cols[-2]:
        if st.session_state.get("authenticated", False):
            _dept_display = ", ".join(st.session_state.get("dept_access", [])) or "All"
            st.markdown(
                f'<div class="top-nav-user" style="color: #FFFFFF;">{st.session_state.get("user_email", "User")}'
                f'<br><span class="top-nav-role" style="color: #CBD5E1;">'
                f'{st.session_state.get("role", "").title()} • {_dept_display}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="top-nav-user" style="color: #FFFFFF;">Public Visitor<br><span class="top-nav-role" style="color: #CBD5E1;">Unauthenticated</span></div>', unsafe_allow_html=True)

    with nav_cols[-1]:
        if st.session_state.get("authenticated", False):
            if st.button("Log out", key="top_logout_btn", use_container_width=True, type="secondary"):
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
        else:
            if st.button("Log In", key="top_login_btn", use_container_width=True, type="primary"):
                st.session_state.show_login = True
                st.rerun()

    # ---- Row 2: Public Resources search/filter/pick + admin shortcuts ----
    if page == "Public Resources" and st.session_state.get("authenticated", False):
        st.markdown('<hr class="top-nav-divider">', unsafe_allow_html=True)
        browsing = st.session_state.get("resource_view", "browse") == "browse"

        if browsing:
            col_mode, col_resources, col_management = st.columns([1, 2, 1])
            with col_mode:
                with st.container(key="mode-card"):
                    st.markdown('<div class="ui-card-title">📋 View Mode</div>', unsafe_allow_html=True)
                    view_mode = st.radio("Mode", ["Single Resource", "Full Catalog"], horizontal=True, key="pr_view_mode", label_visibility="collapsed")

            with col_resources:
                if st.session_state.get("pr_view_mode") == "Single Resource":

                    with st.container(key="resources-card"):
                        st.markdown('<div class="ui-card-title">🔍 Search & Browse</div>', unsafe_allow_html=True)
                        search_col, cat_col, pick_col = st.columns(3, gap="medium")
                        with search_col:
                            st.text_input(
                                "Search by name, business, or category",
                                placeholder="e.g. VAT, URA, Website",
                                key="pr_search_term",
                                label_visibility="collapsed",
                            )
                        with cat_col:
                            _available_categories = (
                                sorted([str(c) for c in _visible_resources_df["category"].dropna().unique() if str(c).strip()])
                                if not _visible_resources_df.empty else []
                            )
                            st.multiselect("Filter by Category", options=_available_categories, key="pr_selected_categories", label_visibility="collapsed")
                        with pick_col:
                            _pick_options = _visible_resources_df["business_name"].tolist() if not _visible_resources_df.empty else []
                            if _pick_options:
                                st.selectbox("Choose a resource to view", options=_pick_options, key="pr_resource_select", label_visibility="collapsed")

            user_id = st.session_state.get("user_id")
            if is_admin or user_id:
                with col_management:
                    with st.container(key="management-card"):
                        st.markdown('<div class="ui-card-title">⚙️ Management</div>', unsafe_allow_html=True)
                        if is_admin:
                            add_col, edit_col = st.columns(2, gap="small")
                            with add_col:
                                if st.button("➕ Add Resource", type="primary", use_container_width=True, key="nav_add_resource_btn"):
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
                        else:
                            if st.button("💡 Suggest a Resource", use_container_width=True, key="nav_suggest_resource_btn"):
                                st.session_state.resource_view = "add"
                                st.rerun()

from core.db_announcements import announcements_get_active
dept_id = None
if st.session_state.get("authenticated", False):
    try:
        from core.db_users import user_get_by_email
        user_row = user_get_by_email(st.session_state.get("user_email"))
        if user_row is not None:
            dept_id = user_row.get("department_id")
    except Exception:
        pass

active_announcements = announcements_get_active(dept_id)
if not active_announcements.empty:
    st.markdown('<div style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)
    for _, ann in active_announcements.iterrows():
        ann_title = str(ann['title'])
        ann_body = str(ann['body'])

        # Format the exact wording to have bold headers and line breaks
        ann_body = ann_body.replace("What to Expect", "<br><br><strong class='maintenance-section-label'>What to Expect</strong><br>")
        ann_body = ann_body.replace("System Downtime:", "<strong>System Downtime:</strong>")
        ann_body = ann_body.replace("Data Safety:", "<strong>Data Safety:</strong>")
        ann_body = ann_body.replace("Automatic Recovery:", "<strong>Automatic Recovery:</strong>")
        ann_body = ann_body.replace("Next Steps", "<br><br><strong class='maintenance-section-label'>Next Steps</strong><br>")

        banner_html = f"""
        <div class="maintenance-banner">
            <div class="maintenance-header">
                <span class="maintenance-icon">📢</span>
                <span class="maintenance-title">{ann_title}</span>
            </div>
            <div class="maintenance-body">
                {ann_body}
            </div>
        </div>
        """
        st.markdown(banner_html, unsafe_allow_html=True)
    st.markdown('<div style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)

if st.session_state.get("authenticated", False):
    if page == "Public Resources":
        render_public_resources()
    elif page == "User Management" and is_admin:
        render_user_management()
    elif page == "Analytics" and is_admin:
        render_analytics()
    elif page == "Governance" and is_admin:
        from views.governance import render_governance
        render_governance()
else:
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

    with st.container(key="auth_split_container"):
        col_brand, col_auth = st.columns([1.1, 0.9], gap="small")

        with col_brand:
            st.markdown("""
<div class="auth-brand-content">
    <h1 class="brand-title">URA Tax Analytics<br>& Resource Portal</h1>
    <p class="brand-subtitle">DEVELOPING UGANDA TOGETHER</p>
    <div class="brand-accent-line"></div>
    <p class="brand-text">Secure, institutional access to national revenue data, interactive tax resources, and automated analytics.</p>
</div>
            """, unsafe_allow_html=True)

        with col_auth:
            st.markdown("""
<div class="auth-action-content">
    <h2 class="auth-title">Authentication Required</h2>
    <p class="auth-description">
        Welcome to the <strong>URA Tax Analytics &amp; Resource Portal</strong>. Public visitors can view active announcements above.
        <br><br>
        To search, filter, and access interactive tax resources, Power BI reports, or account management, please log in or create an account below.
    </p>
</div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
            with c2:
                if st.button("🔐 Log In / Create Account", key="unauth_login_btn_split", type="primary", use_container_width=True):
                    st.session_state.show_login = True
                    st.rerun()