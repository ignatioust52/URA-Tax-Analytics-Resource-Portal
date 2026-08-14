import textwrap
import re

auth_file = "core/auth.py"

with open(auth_file, "r") as f:
    content = f.read()

# Re-write check_login function without inline <style> block and with textwrap.dedent
new_check_login = '''def check_login():
    import textwrap
    from core.utils import render_logo_html
    from core.db_departments import user_department_access_get, departments_get_all
    from core.db_users import users_register
    if st.session_state.get("authenticated", False):
        return True

    logo_left = render_logo_html(48)
    logo_right = render_logo_html(52)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        left_html = textwrap.dedent(f"""
            <div class="login-left-pane">
                <div class="bg-circle-1"></div>
                <div class="bg-circle-2"></div>
                <div class="login-left-header">
                    {logo_left}
                    <div>
                        <div class="login-brand-title">TAX <span>DASHBOARD</span> SYSTEM</div>
                        <div class="login-brand-subtitle">Uganda Revenue Authority</div>
                    </div>
                </div>
                
                <div class="login-illustration-container">
                    <div class="login-doc-card">
                        <div class="login-doc-top-bar"></div>
                        <div class="login-doc-line long"></div>
                        <div class="login-doc-line medium"></div>
                        <div class="login-doc-line long"></div>
                        <div class="login-doc-line short"></div>
                        <div class="login-doc-row">
                            <div class="login-doc-icon green">✓</div>
                            <div class="login-doc-pill"></div>
                        </div>
                        <div class="login-doc-row">
                            <div class="login-doc-icon orange">!</div>
                            <div class="login-doc-pill"></div>
                        </div>
                        <div class="login-doc-row">
                            <div class="login-doc-icon gray"></div>
                            <div class="login-doc-pill"></div>
                        </div>
                        <div class="login-doc-bottom-pill"></div>
                    </div>
                    <div class="login-badge-top-right">
                        <div class="login-badge-top-right-inner">✓</div>
                    </div>
                    <div class="login-badge-plus">+</div>
                    <div class="login-badge-bottom-right">✓</div>
                </div>
                
                <div style="z-index: 2; color: rgba(255,255,255,0.7); font-size: 0.8rem;">
                    © Uganda Revenue Authority — Tax Operations Platform
                </div>
            </div>
        """)
        st.markdown(left_html, unsafe_allow_html=True)

    with col_right:
        right_header_html = textwrap.dedent(f"""
            <div class="login-card-header">
                {logo_right}
                <div class="login-card-header-title">TAX <span>DASHBOARD</span> SYSTEM</div>
                <div class="login-card-header-sub">Uganda Revenue Authority</div>
            </div>
        """)
        st.markdown(right_header_html, unsafe_allow_html=True)

        tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

        # ── Sign In ──────────────────────────────────────────────────
        with tab_signin:
            with st.container(border=True):
                st.markdown('<div class="login-title">Sign in to your account</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="login-subtitle">Enter your credentials to access the Tax Dashboard System.</div>',
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    email_input = st.text_input(
                        "Email Address", value="", placeholder="e.g. user@ura.go.ug"
                    )
                    password_input = st.text_input("Password", type="password")
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

                    if _errors:
                        for err in _errors:
                            st.error(err)
                    else:
                        final_dept = (
                            reg_dept_other.strip()
                            if reg_dept_select == "Other (please specify)"
                            else reg_dept_select
                        )
                        success, msg = users_register(clean_email, reg_password, final_dept)
                        if success:
                            st.success(
                                "Account creation request submitted! An administrator must approve your account before you can log in."
                            )
                        else:
                            st.error(msg)
'''

idx = content.find("def check_login():")
if idx != -1:
    new_content = content[:idx] + new_check_login
    with open(auth_file, "w") as f:
        f.write(new_content)
    print("SUCCESS: Re-wrote check_login with textwrap.dedent")
else:
    print("ERROR: Could not find def check_login()")

