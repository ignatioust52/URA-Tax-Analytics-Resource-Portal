import bcrypt
import secrets
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from core.db import get_connection

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
    conn = get_connection()
    query = """
        SELECT u.*, r.name as role_name, r.hierarchy_level 
        FROM app_users u 
        LEFT JOIN roles r ON u.role_id = r.role_id 
        WHERE u.email = %s
    """
    df = pd.read_sql(query, conn, params=(email.strip().lower(),))
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


def check_login():
    """The sign-in / register screen. Same navy-left / white-right split
    the mockup uses for its login screen and that the pre-login gate page
    in app.py already shows — the CSS classes here (login-hero-*,
    login-card-*, login-title, login-subtitle) are all defined in
    assets/style.css so this reuses the exact same design system instead
    of introducing a second visual style for login."""
    import textwrap
    from core.utils import render_logo_html
    from core.db_departments import user_department_access_get, departments_get_all
    from core.db_users import users_register
    if st.session_state.get("authenticated", False):
        return True

    logo_left = render_logo_html(44)
    logo_right = render_logo_html(48)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown(
            f"""
            <div class="login-hero-panel">
                <div>
                    <div style="margin-bottom: 1.5rem;">{logo_left}</div>
                    <div class="login-hero-title">URA TAX <span>ANALYTICS</span><br>PLATFORM</div>
                    <div class="brand-accent-line"></div>
                    <div class="login-hero-sub">Official Digital Resource &amp; Governance Portal of the Uganda Revenue Authority</div>
                </div>
                <div class="login-hero-footer">
                    🔒 <strong>Secure Enterprise Access</strong><br>
                    Authorized access only. All activities are monitored and audited for compliance and governance.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        # Use inner columns to center the authentication card horizontally on the right side (~450px)
        _, col_auth, _ = st.columns([0.1, 0.8, 0.1])
        
        with col_auth:
            right_header_html = textwrap.dedent(f"""
                <div class="login-card-header">
                    {logo_right}
                    <div class="login-card-header-title">URA TAX <span>ANALYTICS</span> PLATFORM</div>
                    <div class="login-card-header-sub">Uganda Revenue Authority</div>
                </div>
            """)
            st.html(right_header_html)

            tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

            # ── Sign In ──────────────────────────────────────────────────
            with tab_signin:
                with st.form("login_form", clear_on_submit=True):
                    st.markdown('<div class="login-title">Sign in to your account</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="login-subtitle">Enter your credentials to access tax analytics, reports, and resources.</div>',
                        unsafe_allow_html=True,
                    )
                    email_input = st.text_input(
                        "Email Address", value="", placeholder="e.g. user@ura.go.ug", key="login_email"
                    )
                    password_input = st.text_input("Password", type="password", key="login_password")
                    submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

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
                            role = str(user.get("role_name", "")).lower()
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
                                st.session_state.dept_access = user_department_access_get(
                                    int(user["id"])
                                )
                                _session_token = create_user_session(int(user["id"]))
                                st.query_params["session_token"] = _session_token
                                from core.db_audit import log_event as _log
                                _log(str(user["email"]), "login")
                                
                                # Clear form inputs
                                if "login_email" in st.session_state: del st.session_state["login_email"]
                                if "login_password" in st.session_state: del st.session_state["login_password"]
                                
                                st.rerun()
                            else:
                                st.error("Invalid email or password.")

            # ── Create Account ────────────────────────────────────────────────
            with tab_register:
                with st.form("register_form", clear_on_submit=True):
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

                    reg_submitted = st.form_submit_button(
                        "Create Account",
                        use_container_width=True,
                        type="primary",
                    )

                if reg_submitted:
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

                    if _errors:
                        for err in _errors:
                            st.error(err)
                    else:
                        final_dept = (
                            reg_dept_other.strip()
                            if reg_dept_select == "Other (please specify)"
                            else reg_dept_select
                        )
                        _register_result = users_register(clean_email, reg_password, final_dept)
                        if isinstance(_register_result, tuple):
                            success, msg = _register_result
                        else:
                            # users_register returns just the new user id (or None/False) on some code paths
                            success = bool(_register_result)
                            msg = "Account created — awaiting admin approval." if success else "Registration failed."
                        if success:
                            for k in ["reg_email", "reg_password", "reg_confirm", "reg_dept_other", "reg_dept_select"]:
                                if k in st.session_state: del st.session_state[k]
                            st.success(
                                "Account creation request submitted! An administrator must approve your account before you can log in."
                            )
                        else:
                            st.error(msg)