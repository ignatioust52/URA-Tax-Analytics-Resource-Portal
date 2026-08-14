import re
import textwrap

# 1. Update assets/style.css with compact auth CSS rules
css_rules = """

/* ==========================================================================
   ENTERPRISE COMPACT AUTHENTICATION PORTAL STYLES (URA BRANDING)
   ========================================================================== */

/* Zero out padding for seamless login layout */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* Left Pane Styling */
.login-left-pane {
    background: linear-gradient(145deg, #18306D 0%, #243F8D 65%, #12224A 100%);
    width: 100%;
    min-height: 85vh;
    border-radius: 16px;
    padding: 3rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    box-shadow: 0 12px 32px rgba(24, 48, 109, 0.18);
}

.login-left-header {
    display: flex;
    align-items: center;
    gap: 14px;
    z-index: 2;
}

.login-brand-title {
    color: #FFFFFF;
    font-size: 1.15rem;
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
    margin-top: 2px;
}

.login-illustration-wrapper {
    position: relative;
    text-align: center;
    margin: 2rem auto;
    z-index: 2;
    max-width: 360px;
}
.login-illustration-wrapper img {
    max-width: 100%;
    height: auto;
    max-height: 290px;
    filter: drop-shadow(0 12px 24px rgba(0,0,0,0.18));
}

.login-left-footer {
    z-index: 2;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.825rem;
    font-weight: 500;
    text-align: center;
    letter-spacing: 0.2px;
}

/* Background Circles */
.bg-circle-1 {
    position: absolute;
    width: 450px;
    height: 450px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 70%);
    top: -120px;
    right: -120px;
    pointer-events: none;
}
.bg-circle-2 {
    position: absolute;
    width: 550px;
    height: 550px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255,242,0,0.04) 0%, rgba(255,242,0,0) 70%);
    bottom: -180px;
    left: -180px;
    pointer-events: none;
}

/* Right Pane & Compact Auth Form Container */
.login-right-pane {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 85vh;
    padding: 1rem 0;
}

/* Constrain right side max-width so input fields do NOT stretch across the screen */
.auth-compact-card {
    max-width: 460px !important;
    width: 100% !important;
    margin: 0 auto !important;
}

.login-card-header {
    text-align: center;
    margin-bottom: 1.25rem;
}
.login-card-header-title {
    font-size: 1.35rem;
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
    margin-top: 2px;
}

/* Tab Header Styling */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 12px !important;
    border-bottom: 2px solid #E2E8F0 !important;
    margin-bottom: 1.25rem !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 40px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #64748B !important;
    padding: 0 16px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #243F8D !important;
    border-bottom-color: #243F8D !important;
}

/* Input Fields Styling (Compact, Elegant, Fixed Height) */
div[data-baseweb="input"] {
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    height: 46px !important;
    transition: all 0.2s ease;
}
div[data-baseweb="input"]:focus-within {
    border-color: #243F8D !important;
    box-shadow: 0 0 0 3px rgba(36, 63, 141, 0.12) !important;
}
div[data-baseweb="input"] input {
    color: #0F172A !important;
    font-size: 0.925rem !important;
    padding: 0 12px !important;
}

/* Selectbox Styling */
div[data-baseweb="select"] > div {
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    height: 46px !important;
}

/* Form Container Card Refinement */
[data-testid="stForm"] {
    border-radius: 12px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01) !important;
    padding: 2rem 2.25rem !important;
    background: #FFFFFF !important;
}

/* Form Headings */
.login-title {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    margin-bottom: 4px !important;
}
.login-subtitle {
    font-size: 0.85rem !important;
    color: #64748B !important;
    margin-bottom: 1.25rem !important;
    line-height: 1.4 !important;
}

/* Primary Button Styling (Sign In / Create Account) */
div[data-testid="stForm"] button[type="submit"],
button[key="register_btn"] {
    height: 46px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    background-color: #243F8D !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    margin-top: 0.5rem !important;
}
div[data-testid="stForm"] button[type="submit"]:hover,
button[key="register_btn"]:hover {
    background-color: #18306D !important;
    box-shadow: 0 4px 12px rgba(36, 63, 141, 0.25) !important;
}

"""

with open("assets/style.css", "a") as f:
    f.write("\n" + css_rules)

print("CSS appended to assets/style.css")

# 2. Update core/auth.py with centered compact layout structure
img_path = "/home/feza/.gemini/antigravity-ide/brain/1a544fcb-7286-4757-b9f8-f524f7d60499/.user_uploaded/media_1786672691643.png"
import base64
with open(img_path, "rb") as f_in:
    img_data = f_in.read()

b64_img = base64.b64encode(img_data).decode("utf-8")
data_uri = f"data:image/png;base64,{b64_img}"

auth_file = "core/auth.py"
with open(auth_file, "r") as f:
    content = f.read()

new_check_login = f'''def check_login():
    import textwrap
    from core.utils import render_logo_html
    from core.db_departments import user_department_access_get, departments_get_all
    from core.db_users import users_register
    if st.session_state.get("authenticated", False):
        return True

    logo_left = render_logo_html(44)
    logo_right = render_logo_html(48)

    # 50/50 split layout: Left side branding/illustration, Right side centered compact form
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        left_html = textwrap.dedent(f"""
            <div class="login-left-pane">
                <div class="bg-circle-1"></div>
                <div class="bg-circle-2"></div>
                <div class="login-left-header">
                    {{logo_left}}
                    <div>
                        <div class="login-brand-title">URA TAX <span>ANALYTICS</span> PLATFORM</div>
                        <div class="login-brand-subtitle">Uganda Revenue Authority</div>
                    </div>
                </div>
                
                <div class="login-illustration-wrapper">
                    <img src="{data_uri}" alt="Tax Analytics Illustration" />
                </div>
                
                <div class="login-left-footer">
                    🔒 Secure Access to Tax Analytics & Revenue Intelligence
                </div>
            </div>
        """)
        st.html(left_html)

    with col_right:
        # Use inner columns to center the authentication card horizontally on the right side (~450px)
        _, col_auth, _ = st.columns([0.1, 0.8, 0.1])
        
        with col_auth:
            right_header_html = textwrap.dedent(f"""
                <div class="login-card-header">
                    {{logo_right}}
                    <div class="login-card-header-title">URA TAX <span>ANALYTICS</span> PLATFORM</div>
                    <div class="login-card-header-sub">Uganda Revenue Authority</div>
                </div>
            """)
            st.html(right_header_html)

            tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

            # ── Sign In ──────────────────────────────────────────────────
            with tab_signin:
                with st.form("login_form"):
                    st.markdown('<div class="login-title">Sign in to your account</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="login-subtitle">Enter your credentials to access tax analytics, reports, and resources.</div>',
                        unsafe_allow_html=True,
                    )
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
                with st.form("register_form"):
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
    print("SUCCESS: Compact Auth Portal layout updated")
else:
    print("ERROR: Could not find def check_login()")

