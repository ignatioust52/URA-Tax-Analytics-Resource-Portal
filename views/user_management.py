"""
views/user_management.py — Admin User Management page rendering.

Entry point: render_user_management()

Six tabs:
  1. Pending Approvals    — approve/reject self-registered accounts
  2. Active Users         — view, toggle, edit role/depts, reset pwd, delete
  3. Special Permissions  — ABAC-style permission overrides
  4. Create Account       — admin-direct bypass of the registration queue
  5. Audit Trail          — recent platform activity log
  6. Announcements        — broadcast messages to all users or a department

No SQL lives here; all DB calls go through core.db_users and core.db_departments.
Email notifications are sent via email_utils after each action.

STYLE: every card on this page is a plain st.container(border=True) — the
".ui-card" look (triband hairline top-accent, flat border, hover state)
comes for free from style.css's [data-testid="stVerticalBlockBorderWrapper"]
rule, so no per-card class or inline <style> is needed here. Section
headers use the shared ".section-title" / ".section-sub" classes so this
page reads as part of the same product as Dashboard and Public Resources.
"""

import streamlit as st
import email_utils

from core.utils import humanize_dt
from core.auth import is_password_strong
from core.db_departments import (
    departments_get_all,
    departments_create,
    departments_update,
    departments_delete,
    user_department_access_get,
)
from core.db_users import (
    users_get_all,
    users_get_pending,
    users_create,
    users_approve,
    users_reject,
    users_toggle_active,
    users_delete,
    users_update_role_department,
    users_reset_password,
    users_get_special_permissions,
    users_grant_special_permission,
    users_revoke_special_permission,
)
from core.db_announcements import (
    announcements_get_all,
    announcements_create,
    announcements_update,
    announcements_delete,
)


def render_user_management():
    is_admin = st.session_state.get("role") == "admin"
    if not is_admin:
        st.warning("Access restricted to administrators.")
        return

    st.markdown('<div class="section-title">Admin User Management</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Approve accounts, manage roles and department access, '
        'and broadcast announcements.</div>',
        unsafe_allow_html=True,
    )

    tab_pending, tab_active, tab_abac, tab_create, tab_audit, tab_announce = st.tabs(
        ["Pending Approvals", "Active Users", "Special Permissions", "Create Account", "Audit Trail", "Announcements"]
    )

    # ── TAB 1: Pending Approvals ─────────────────────────────────────────
    with tab_pending:
        pending_df = users_get_pending()

        if pending_df.empty:
            st.info("No pending registration requests at this time.")
        else:
            st.markdown(
                f'<span class="ura-chip ura-chip-gold">{len(pending_df)} account(s) awaiting approval</span>',
                unsafe_allow_html=True,
            )
            st.markdown('<div style="margin-top: 0.9rem;"></div>', unsafe_allow_html=True)

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
                            "Approve",
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
                            "Reject",
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
        with st.container(border=True):
            st.markdown('<div class="ui-card-title">Existing User Accounts</div>', unsafe_allow_html=True)
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

                st.markdown('<div class="section-title" style="font-size: 0.95rem; margin-top: 1.1rem;">Manage User Account</div>', unsafe_allow_html=True)
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
                    ["Toggle Status", "Role & Departments", "Reset Password", "Delete"]
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
                    if st.button("Delete Account Permanently", use_container_width=True, key="btn_delete", disabled=not confirm_delete):
                        success, msg = users_delete(managed_uid)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    # ── TAB 3: Special Permissions (ABAC) ─────────────────────────────────
    with tab_abac:
        with st.container(border=True):
            st.markdown('<div class="ui-card-title">Special Permissions (ABAC)</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-sub">Grant specialized access overrides to users '
                '(e.g. <code>export.large</code>, <code>view.sensitive</code>).</div>',
                unsafe_allow_html=True,
            )

            _abac_users_df = users_get_all()
            if not _abac_users_df.empty:
                active_only = _abac_users_df[_abac_users_df["is_active"] == True]
                if not active_only.empty:
                    abac_user = st.selectbox("Select User", options=active_only["email"].tolist(), key="abac_user_sel")
                    if abac_user:
                        u_row = active_only[active_only["email"] == abac_user].iloc[0]
                        u_id = u_row["id"]

                        st.markdown('<div class="section-title" style="font-size: 0.92rem; margin-top: 0.75rem;">Granted Permissions</div>', unsafe_allow_html=True)
                        perms = users_get_special_permissions(u_id)
                        if not perms:
                            st.info("No special permissions granted.")
                        else:
                            for p in perms:
                                with st.container(border=True):
                                    col_p, col_r = st.columns([4, 1])
                                    col_p.markdown(
                                        f'<span class="ura-chip ura-chip-blue">{p["permission_key"]}</span> '
                                        f'&nbsp;Reason: {p["reason"] or "N/A"}',
                                        unsafe_allow_html=True,
                                    )
                                    if col_r.button("Revoke", key=f"revoke_{p['id']}", use_container_width=True):
                                        users_revoke_special_permission(p["id"])
                                        st.rerun()

                        st.markdown('<div class="section-title" style="font-size: 0.92rem; margin-top: 0.9rem;">Grant New Permission</div>', unsafe_allow_html=True)
                        with st.form("grant_abac_form", clear_on_submit=True):
                            new_key = st.text_input("Permission Key (e.g. export.large)", key="grant_abac_key")
                            reason = st.text_input("Reason", key="grant_abac_reason")
                            if st.form_submit_button("Grant Permission", type="primary"):
                                if new_key.strip():
                                    users_grant_special_permission(u_id, new_key.strip(), st.session_state.get("user_id"), reason)
                                    st.success("Permission granted!")
                                    if "grant_abac_key" in st.session_state: del st.session_state["grant_abac_key"]
                                    if "grant_abac_reason" in st.session_state: del st.session_state["grant_abac_reason"]
                                    st.rerun()
                                else:
                                    st.error("Key is required.")

    # ── TAB 4: Create Account ─────────────────────────────────────────────
    with tab_create:
        with st.container(border=True):
            st.markdown('<div class="ui-card-title">Create New User Account</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-sub">Admin bypass — account is created as active immediately, '
                'skipping the self-registration approval queue.</div>',
                unsafe_allow_html=True,
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
                            if st.button("Save", key=f"save_dept_{_dept_id_e}", use_container_width=True):
                                if _renamed.strip() and _renamed.strip() != _erow["name"]:
                                    success, msg = departments_update(_dept_id_e, _renamed.strip())
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        with _del_col:
                            if st.button("Delete", key=f"delete_dept_{_dept_id_e}", use_container_width=True):
                                success, msg = departments_delete(_dept_id_e)
                                if success:
                                    st.success(f"Deleted '{_erow['name']}'.")
                                    st.rerun()
                                else:
                                    st.error(msg)

            with st.form("create_user_form", clear_on_submit=True):
                new_email = st.text_input("User Email", placeholder="e.g. officer@ura.go.ug", key="create_user_email")
                new_password = st.text_input("Temporary Password", type="password", key="create_user_pwd")
                new_role = st.selectbox("Role", options=["viewer", "admin"], key="create_user_role")

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

                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

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
                                if "create_user_email" in st.session_state: del st.session_state["create_user_email"]
                                if "create_user_pwd" in st.session_state: del st.session_state["create_user_pwd"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to create user: {e}")

    # ── TAB 5: Audit Trail ────────────────────────────────────────────────
    with tab_audit:
        with st.container(border=True):
            st.markdown('<div class="ui-card-title">Activity Audit Log</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-sub">Most recent 200 platform events, newest first.</div>',
                unsafe_allow_html=True,
            )

            from core.db_audit import get_audit_log
            audit_df = get_audit_log(limit=200)

            if audit_df.empty:
                st.info("No audit events recorded yet.")
            else:
                disp_audit = audit_df.copy()
                disp_audit["logged_at"] = disp_audit["logged_at"].apply(humanize_dt)
                disp_audit.columns = ["ID", "Time", "Actor", "Action", "Resource Type", "Resource", "Details"]
                st.dataframe(disp_audit, use_container_width=True, height=500, hide_index=True)

    # ── TAB 6: Announcements ─────────────────────────────────────────────
    with tab_announce:
        st.markdown('<div class="section-title" style="font-size: 1rem;">Manage Announcements</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-sub">Broadcast messages to all users or specific departments.</div>',
            unsafe_allow_html=True,
        )

        with st.expander("➕ Create New Announcement", expanded=False, icon=":material/add:"):
            with st.form("new_announce_form", clear_on_submit=True):
                title = st.text_input("Title (e.g. Scheduled Maintenance)", key="ann_title")
                body = st.text_area("Message Body", key="ann_body")
                dept_df = departments_get_all()
                dept_options = {"All Departments (Global)": None}
                for _, d in dept_df.iterrows():
                    dept_options[d["name"]] = int(d["id"])
                dept_choice = st.selectbox("Target Audience", options=list(dept_options.keys()))

                submitted = st.form_submit_button("Publish Announcement", type="primary")
                if submitted:
                    if not title or not body:
                        st.error("Title and body are required.")
                    else:
                        announcements_create(
                            title, body, dept_options[dept_choice],
                            st.session_state.get("user_email")
                        )
                        st.success("Announcement published!")
                        if "ann_title" in st.session_state: del st.session_state["ann_title"]
                        if "ann_body" in st.session_state: del st.session_state["ann_body"]
                        st.rerun()

        ann_df = announcements_get_all()
        if ann_df.empty:
            st.info("No announcements found.")
        else:
            for _, ann in ann_df.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{ann['title']}**")
                        st.caption(f"Published by {ann['published_by']} on {humanize_dt(ann['published_at'])}")
                        st.markdown(ann["body"])
                    with col2:
                        status_chip = (
                            '<span class="ura-chip ura-chip-green">Active</span>' if ann["is_active"]
                            else '<span class="ura-chip ura-chip-red">Inactive</span>'
                        )
                        st.markdown(status_chip, unsafe_allow_html=True)
                        if st.button("Delete", key=f"del_ann_{ann['announcement_id']}", icon=":material/delete:", use_container_width=True):
                            announcements_delete(ann["announcement_id"])
                            st.rerun()
                        if st.button("Toggle Status", key=f"tgl_ann_{ann['announcement_id']}", icon=":material/toggle_on:", use_container_width=True):
                            announcements_update(
                                ann["announcement_id"], ann["title"], ann["body"],
                                ann["audience_department_id"], ann["expires_at"], not ann["is_active"]
                            )
                            st.rerun()