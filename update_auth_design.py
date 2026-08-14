import re

auth_file = "core/auth.py"

with open(auth_file, "r") as f:
    content = f.read()

# Custom CSS and HTML layout for check_login()
login_css_and_layout = '''
    # Inject page-level CSS overrides for seamless edge-to-edge split login
    st.markdown("""
        <style>
        /* Flush container for login page */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        .login-split-container {
            display: flex;
            min-height: 100vh;
            width: 100vw;
            background-color: #F8FAFC;
        }
        
        /* LEFT SIDE */
        .login-left-pane {
            background: linear-gradient(145deg, #1B367A 0%, #243F8D 60%, #15295C 100%);
            width: 50%;
            min-height: 100vh;
            padding: 3rem 4rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            box-shadow: 4px 0 24px rgba(0,0,0,0.12);
        }
        
        .login-left-header {
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 2;
        }
        
        .login-brand-title {
            color: #FFFFFF;
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            line-height: 1.2;
        }
        .login-brand-title span {
            color: #FFF200;
        }
        .login-brand-subtitle {
            color: rgba(255, 255, 255, 0.75);
            font-size: 0.8rem;
            font-weight: 400;
        }
        
        /* Graphic illustration */
        .login-illustration-container {
            position: relative;
            width: 320px;
            height: 380px;
            margin: 2rem auto;
            z-index: 2;
        }
        
        .login-doc-card {
            width: 240px;
            height: 310px;
            background: #FFFFFF;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.25);
            position: absolute;
            left: 20px;
            top: 40px;
            padding: 24px 20px;
            overflow: hidden;
        }
        .login-doc-top-bar {
            height: 12px;
            background: #FFF200;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .login-doc-line {
            height: 8px;
            background: #4C74B2;
            opacity: 0.4;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .login-doc-line.short { width: 50%; }
        .login-doc-line.medium { width: 75%; }
        .login-doc-line.long { width: 100%; }
        
        .login-doc-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 16px;
        }
        .login-doc-icon {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }
        .login-doc-icon.green { background: #008751; }
        .login-doc-icon.orange { background: #F97316; }
        .login-doc-icon.gray { background: #CBD5E1; }
        .login-doc-pill {
            height: 8px;
            background: #EDEFF6;
            border-radius: 4px;
            flex-grow: 1;
        }
        
        .login-doc-bottom-pill {
            height: 12px;
            background: #243F8D;
            border-radius: 6px;
            width: 70px;
            margin-top: 24px;
        }
        
        /* Floating badge elements */
        .login-badge-top-right {
            position: absolute;
            top: 10px;
            right: 15px;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: #FFF200;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }
        .login-badge-top-right-inner {
            width: 46px;
            height: 46px;
            border-radius: 50%;
            background: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #243F8D;
            font-size: 24px;
            font-weight: bold;
        }
        .login-badge-plus {
            position: absolute;
            right: 0px;
            top: 190px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.4);
            background: rgba(36, 63, 141, 0.6);
            backdrop-filter: blur(4px);
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
        }
        .login-badge-bottom-right {
            position: absolute;
            bottom: 0px;
            right: 50px;
            width: 62px;
            height: 62px;
            border-radius: 50%;
            background: #008751;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            font-weight: bold;
            box-shadow: 0 10px 20px rgba(0,135,81,0.3);
            border: 4px solid #FFFFFF;
        }
        
        /* Background circles */
        .bg-circle-1 {
            position: absolute;
            width: 500px;
            height: 500px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 70%);
            top: -150px;
            right: -150px;
            pointer-events: none;
        }
        .bg-circle-2 {
            position: absolute;
            width: 600px;
            height: 600px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,242,0,0.04) 0%, rgba(255,242,0,0) 70%);
            bottom: -200px;
            left: -200px;
            pointer-events: none;
        }

        /* RIGHT SIDE */
        .login-right-pane {
            width: 50%;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem 2rem;
        }
        
        .login-card-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .login-card-header-title {
            font-size: 1.4rem;
            font-weight: 800;
            color: #243F8D;
            margin-top: 10px;
            letter-spacing: 0.5px;
        }
        .login-card-header-title span {
            color: #7F7801;
        }
        .login-card-header-sub {
            color: #636363;
            font-size: 0.85rem;
        }
        
        .login-form-card {
            background: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            padding: 2.5rem;
            width: 100%;
            max-width: 440px;
        }
        
        .login-form-card .login-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .login-form-card .login-subtitle {
            font-size: 0.875rem;
            color: #636363;
            margin-bottom: 1.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
'''

# Find check_login function in content
pattern = re.compile(r'def check_login\(\):.*', re.DOTALL)

# Let's rebuild check_login cleanly
new_check_login = '''def check_login():
    from core.utils import render_logo_html
    from core.db_departments import user_department_access_get, departments_get_all
    from core.db_users import users_register
    if st.session_state.get("authenticated", False):
        return True

''' + login_css_and_layout + '''

    logo_left = render_logo_html(48)
    logo_right = render_logo_html(52)

    # 50/50 Layout using st.columns with gap=None
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown(f"""
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
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
            <div class="login-card-header">
                {logo_right}
                <div class="login-card-header-title">TAX <span>DASHBOARD</span> SYSTEM</div>
                <div class="login-card-header-sub">Uganda Revenue Authority</div>
            </div>
        """, unsafe_allow_html=True)

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

# Replace def check_login onwards
idx = content.find("def check_login():")
if idx != -1:
    new_content = content[:idx] + new_check_login
    with open(auth_file, "w") as f:
        f.write(new_content)
    print("SUCCESS: Updated check_login()")
else:
    print("ERROR: Could not find def check_login()")

