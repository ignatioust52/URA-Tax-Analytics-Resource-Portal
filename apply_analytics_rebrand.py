import base64
import os
import textwrap

img_path = "/home/feza/.gemini/antigravity-ide/brain/1a544fcb-7286-4757-b9f8-f524f7d60499/.user_uploaded/media_1786672691643.png"
dest_img = "assets/login_illustration.png"

# Copy image to assets/
with open(img_path, "rb") as f_in:
    img_data = f_in.read()

with open(dest_img, "wb") as f_out:
    f_out.write(img_data)

b64_img = base64.b64encode(img_data).decode("utf-8")
data_uri = f"data:image/png;base64,{b64_img}"

print("Image encoded, size:", len(data_uri))

# Now update core/auth.py
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

    logo_left = render_logo_html(48)
    logo_right = render_logo_html(52)

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
                
                <div class="login-illustration-wrapper" style="position: relative; text-align: center; margin: 1.5rem auto; z-index: 2;">
                    <img src="{data_uri}" style="max-width: 85%; height: auto; max-height: 320px; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.15));" alt="Tax Analytics Illustration" />
                    <div class="login-badge-bottom-right" style="position: absolute; bottom: 10px; right: 20px;">
                        <span class="material-symbols-rounded" style="font-size: 28px;">lock</span>
                    </div>
                </div>
                
                <div style="z-index: 2; color: rgba(255,255,255,0.75); font-size: 0.85rem; font-weight: 500; text-align: center;">
                    🔒 Secure Access to Tax Analytics & Revenue Intelligence
                </div>
            </div>
        """)
        st.html(left_html)

    with col_right:
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
            with st.container(border=True):
                st.markdown('<div class="login-title">Sign in to your account</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="login-subtitle">Enter your credentials to access tax analytics, reports, and resources.</div>',
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
    print("SUCCESS: Updated check_login with Analytics Platform rebrand")
else:
    print("ERROR: Could not find def check_login()")

