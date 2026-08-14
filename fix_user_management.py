import re
with open('views/user_management.py', 'r') as f:
    content = f.read()

abac_ui = """
    # ── TAB: ABAC ──────────────────────────────────────────────
    with tab_abac:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title" style="border-bottom: 1px solid #E3E8EF; padding-bottom: 8px; margin-bottom: 16px;">Special Permissions (ABAC)</div>',
            unsafe_allow_html=True,
        )
        st.write("Grant specialized access overrides to users (e.g. `export.large`, `view.sensitive`).")
        if not users_df.empty:
            active_only = users_df[users_df["is_active"] == True]
            if not active_only.empty:
                abac_user = st.selectbox("Select User", options=active_only["email"].tolist(), key="abac_user_sel")
                if abac_user:
                    u_row = active_only[active_only["email"] == abac_user].iloc[0]
                    u_id = u_row["id"]
                    
                    st.markdown("#### Granted Permissions")
                    perms = users_get_special_permissions(u_id)
                    if not perms:
                        st.info("No special permissions granted.")
                    else:
                        for p in perms:
                            with st.container(border=True):
                                col_p, col_r = st.columns([4, 1])
                                col_p.markdown(f"**`{p['permission_key']}`** — Reason: {p['reason'] or 'N/A'}")
                                if col_r.button("Revoke", key=f"revoke_{p['id']}"):
                                    users_revoke_special_permission(p['id'])
                                    st.rerun()
                    
                    st.markdown("#### Grant New Permission")
                    with st.form("grant_abac_form"):
                        new_key = st.text_input("Permission Key (e.g. export.large)")
                        reason = st.text_input("Reason")
                        if st.form_submit_button("Grant Permission", type="primary"):
                            if new_key.strip():
                                users_grant_special_permission(u_id, new_key.strip(), st.session_state.get("user_id"), reason)
                                st.success("Permission granted!")
                                st.rerun()
                            else:
                                st.error("Key is required.")
        st.markdown('</div>', unsafe_allow_html=True)

"""

content = content.replace(
    '    # ── TAB 3: Create Account ─────────────────────────────────────────────',
    abac_ui + '    # ── TAB 3: Create Account ─────────────────────────────────────────────'
)

with open('views/user_management.py', 'w') as f:
    f.write(content)
