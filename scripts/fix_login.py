import re

with open('core/auth.py', 'r') as f:
    content = f.read()

# Replace the layout logic in check_login()
old_layout = """    st.write("")  # small top spacing so the card isn't glued to the page edge
    col_spacer_l, col_form, col_spacer_r = st.columns([1, 3, 1])
    with col_form:
        left_col, right_col = st.columns([1, 1.2], gap="small")

        with left_col:
            logo_html_inner = render_logo_html(48)
            st.markdown(
                f\"\"\"
                <div class="auth-left-panel">
                    <div class="auth-logo-badge">{logo_html_inner}</div>
                    <div class="auth-left-title">URA Tax Dashboard</div>
                    <div class="auth-left-subtitle">
                        Secure access for URA staff — visualize, explore, and manage
                        tax invoice data in real time.
                    </div>
                </div>
                \"\"\",
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
                )"""

new_layout = """    st.write("")  # small top spacing
    
    # Force full height container via CSS injection
    st.markdown('''
        <style>
        .auth-split-left {
            background-color: #243f8d;
            border-radius: 12px;
            padding: 4rem;
            height: 100%;
            min-height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(36,63,141,0.15);
        }
        .auth-split-left h1 {
            color: #ffffff !important;
            font-size: 2.5rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        .auth-split-left p {
            color: rgba(255,255,255,0.9);
            font-size: 1.2rem;
            line-height: 1.6;
        }
        .auth-split-bg-shape-1 {
            position: absolute;
            width: 400px;
            height: 400px;
            background: rgba(255, 242, 0, 0.05);
            border-radius: 50%;
            top: -100px;
            right: -100px;
        }
        .auth-split-bg-shape-2 {
            position: absolute;
            width: 600px;
            height: 600px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 50%;
            bottom: -200px;
            left: -200px;
        }
        .auth-right-header {
            text-align: center;
            margin-bottom: 2rem;
            margin-top: 2rem;
        }
        .auth-right-header h2 {
            color: #243f8d !important;
            font-size: 1.5rem;
            margin-top: 0.5rem;
        }
        </style>
    ''', unsafe_allow_html=True)

    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        logo_html_inner = render_logo_html(64)
        st.markdown(
            f\"\"\"
            <div class="auth-split-left">
                <div style="z-index: 1;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        {logo_html_inner}
                    </div>
                    <h1>URA Tax Dashboard</h1>
                    <p>
                        Secure access for URA staff — visualize, explore, and manage
                        tax invoice data in real time.
                    </p>
                </div>
                <div class="auth-split-bg-shape-1"></div>
                <div class="auth-split-bg-shape-2"></div>
            </div>
            \"\"\",
            unsafe_allow_html=True,
        )

    with right_col:
        logo_html_inner = render_logo_html(48)
        st.markdown(
            f\"\"\"
            <div class="auth-right-header">
                {logo_html_inner}
                <h2>URA Tax Dashboard</h2>
            </div>
            \"\"\",
            unsafe_allow_html=True,
        )
        
        with st.container(border=True, key="auth-right-panel"):
            tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

            # ── Sign In ──────────────────────────────────────────────────
            with tab_signin:
                st.markdown('<div class="login-title">Sign in to your account</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="login-subtitle">Enter your credentials to access the URA Tax Dashboard.</div>',
                    unsafe_allow_html=True,
                )"""

content = content.replace(old_layout, new_layout)

with open('core/auth.py', 'w') as f:
    f.write(content)
