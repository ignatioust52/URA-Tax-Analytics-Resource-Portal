import streamlit as st
from core.db_resources import (
    resources_get_all,
    test_resource_url,
    resources_create,
    resources_update,
    resources_delete,
    resources_record_view,
    resources_get_audit_log,
    resources_get_favorites,
    resources_get_recent,
    resources_toggle_favorite,
    resources_record_recent
)
from core.db_departments import (
    departments_get_all,
    resource_department_access_get,
    resources_get_department_map
)
from core.utils import humanize_dt
from core.db_announcements import announcements_get_active
from core.db_users import user_get_by_email
from core.db_audit import log_event
from core.db import get_connection
import html as html_lib
import streamlit.components.v1 as components
import pandas as pd
import json

# ---------------------------------------------------------------------------
# The Power BI report navbar below is rendered inside an <iframe> via
# components.html(), so it can't inherit assets/style.css — it needs its own
# color constants. These are the SAME URA design tokens as style.css
# (institutional navy / gold / terracotta), not the old core.constants blue
# theme, so the embedded nav bar reads as part of the same product instead
# of a different app bolted on. If style.css's palette ever changes, update
# these four values to match.
# ---------------------------------------------------------------------------
URA_NAVY = "#243F8D"
URA_NAVY_DARK = "#1A2E66"
URA_NAVY_PALE = "#EAF0F6"
URA_INK = "#1C2430"


def set_single_resource_view(resource_name):
    st.session_state["pr_view_mode"] = "Single Resource"
    st.session_state["pr_resource_select"] = resource_name

def render_public_resources():
    is_admin = st.session_state.get("role") == "admin"
    all_resources_df = resources_get_all()
    if not all_resources_df.empty and "id" in all_resources_df.columns:
        all_resources_df = all_resources_df.drop_duplicates(subset="id", keep="first").reset_index(drop=True)

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
                if res_row.get("approval_status", "Approved") != "Approved":
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
    if st.session_state.get("pr_view_mode") == "Full Catalog":

        
        # We use all_resources_df here so they see things they don't have access to
        st.markdown('<div class="section-title">Public Aggregate Portal</div>', unsafe_allow_html=True)
        
        # Public KPIs
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            st.metric("Total Available Resources", len(all_resources_df))
        with kpi_col2:
            active_cats = len(all_resources_df["category"].dropna().unique()) if not all_resources_df.empty else 0
            st.metric("Total Categories", active_cats)
        with kpi_col3:
            if not all_resources_df.empty and "created_at" in all_resources_df.columns:
                now = pd.Timestamp.now()
                new_this_month = len(all_resources_df[pd.to_datetime(all_resources_df["created_at"]).dt.month == now.month])
            else:
                new_this_month = 0
            st.metric("New This Month", new_this_month)
            
        st.markdown('<br><div class="section-title">URA Quick Services Grid</div>', unsafe_allow_html=True)
        
        user_id = st.session_state.get("user_id")
        
        if user_id:
            tab_all, tab_fav, tab_recent, tab_news, tab_ai = st.tabs(["All Resources", "My Favorites", "Recently Viewed", "News Feed", "AI Assistant"])
        else:
            tab_all, tab_news, tab_ai = st.tabs(["All Resources", "News Feed", "AI Assistant"])
        
        # Helper to render the grid
        def render_grid(df_to_render, context="all"):
            if df_to_render.empty:
                st.markdown(
                    '<div class="ura-empty-state"><div class="icon">📂</div>'
                    '<div class="title">No resources to display</div>'
                    '<div>Nothing matches this view yet.</div></div>',
                    unsafe_allow_html=True,
                )
                return
            # NOTE (Limitation): Streamlit's st.columns() cannot be conditionally set based 
            # on viewport width in pure Python (no native responsive breakpoint API). 
            # We hardcode 3 columns here and rely on CSS media queries in style.css 
            # to adjust widths (e.g. 50% on tablet) and handle mobile stacking.
            cols_per_row = 3
            for i in range(0, len(df_to_render), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(df_to_render):
                        row = df_to_render.iloc[i + j]
                        has_access = row["id"] in resources_df["id"].values
                        
                        with cols[j]:
                            with st.container(border=True):
                                cat_name = str(row.get("category", "Resource")).strip() or "Resource"
                                cat_badge = f'<span class="ura-chip ura-chip-blue">{html_lib.escape(cat_name)}</span>'
                                access_badge = '<span class="ura-chip ura-chip-green">Available</span>' if has_access else '<span class="ura-chip ura-chip-gold">Restricted</span>'
                                st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">{cat_badge}{access_badge}</div>', unsafe_allow_html=True)
                                st.markdown(f"**{html_lib.escape(str(row['business_name']))}**")
                                if row.get('description'):
                                    st.caption(html_lib.escape(str(row['description'])))
                                
                                if has_access:
                                    st.button("View Resource", key=f"cat_view_{context}_{row['id']}", use_container_width=True, type="primary", on_click=set_single_resource_view, args=(row["business_name"],))
                                else:
                                    if st.button("Request Access", key=f"cat_req_{context}_{row['id']}", use_container_width=True):
                                        st.toast(f"Access request sent for {row['business_name']}!")

        user_id = st.session_state.get("user_id")
        
        with tab_all:
            render_grid(all_resources_df, context="all")
            
        if user_id:
            with tab_fav:
                fav_ids = list(dict.fromkeys(resources_get_favorites(user_id)))
                fav_df = all_resources_df[all_resources_df["id"].isin(fav_ids)].reset_index(drop=True)
                render_grid(fav_df, context="fav")
                
            with tab_recent:
                recent_ids_raw = [r[0] if isinstance(r, (tuple, list)) else r for r in resources_get_recent(user_id)]
                recent_ids = list(dict.fromkeys(recent_ids_raw))  # de-dupe, preserve most-recent-first order
                recent_df = all_resources_df[all_resources_df["id"].isin(recent_ids)].copy()
                if not recent_df.empty:
                    recent_df['sorter'] = recent_df['id'].map({id: idx for idx, id in enumerate(recent_ids)})
                    recent_df = recent_df.sort_values('sorter').drop('sorter', axis=1).reset_index(drop=True)
                render_grid(recent_df, context="recent")
        with tab_news:
            dept_id = None
            if user_id:
                try:
                    user_row = user_get_by_email(st.session_state.get("user_email"))
                    if user_row is not None:
                        dept_id = user_row.get("department_id")
                except Exception:
                    pass
            active_announcements = announcements_get_active(dept_id)
            if active_announcements.empty:
                st.markdown(
                    '<div class="ura-empty-state"><div class="icon">📢</div>'
                    '<div class="title">No active announcements</div>'
                    '<div>Check back later for news and updates.</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                for _, ann in active_announcements.iterrows():
                    with st.container(border=True):
                        st.markdown(f"#### 📢 {ann['title']}")
                        st.caption(f"Published on {humanize_dt(ann['published_at'])}")
                        st.markdown(ann['body'])
                        
        with tab_ai:
            st.markdown("### URA AI Assistant")
            st.caption("Ask me anything about URA resources, policies, or navigation!")
            
            # Initialize chat history
            if "ai_messages" not in st.session_state:
                st.session_state.ai_messages = [
                    {"role": "assistant", "content": "Hello! I am your URA AI Assistant. How can I help you today?"}
                ]

            # Display chat messages from history on app rerun
            for message in st.session_state.ai_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # React to user input
            if prompt := st.chat_input("Ask a question..."):
                # Display user message in chat message container
                st.chat_message("user").markdown(prompt)
                # Add user message to chat history
                st.session_state.ai_messages.append({"role": "user", "content": prompt})

                # Mock AI Response
                response = f"I am a mock AI. You asked: '{prompt}'. In the future, this will connect to a real LLM like OpenAI to provide intelligent answers!"
                lower_prompt = prompt.lower()
                if "vat" in lower_prompt:
                    response = "Value Added Tax (VAT) is a tax applied to goods and services. You can find the VAT Calculator in the All Resources tab!"
                elif "password" in lower_prompt or "login" in lower_prompt:
                    response = "If you're having trouble logging in, please contact your department administrator to reset your password."

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                # Add assistant response to chat history
                st.session_state.ai_messages.append({"role": "assistant", "content": response})

        return

    if resources_df.empty:
        st.markdown(
            '<div class="ura-empty-state"><div class="icon">🔒</div>'
            '<div class="title">No resources available</div>'
            '<div>Nothing matches your visibility permissions or filters.</div></div>',
            unsafe_allow_html=True,
        )
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
        st.markdown(
            '<div class="ura-empty-state"><div class="icon">🔍</div>'
            '<div class="title">No matches</div>'
            '<div>No resources match your search.</div></div>',
            unsafe_allow_html=True,
        )
        return

    # Ensure selected_name falls back to first available if missing or invalid
    available_names = list(display_df["business_name"])
    if not selected_name or selected_name not in available_names:
        selected_name = available_names[0]
        st.session_state["pr_resource_select"] = selected_name
    # MAIN AREA — "Add New Resource" page

    # --- URA-BUBBLES FLOATING PANEL ---
    st.markdown(
        """
        <div class="ura-bubbles-container">
            <a href="#" class="ura-bubble">
                <span class="material-symbols-rounded">currency_exchange</span>
                <span class="tooltip">Exchange Rates</span>
            </a>
            <a href="#" class="ura-bubble">
                <span class="material-symbols-rounded">calculate</span>
                <span class="tooltip">Compute Tax</span>
            </a>
            <a href="#" class="ura-bubble">
                <span class="material-symbols-rounded">campaign</span>
                <span class="tooltip">Whistle Blow</span>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

    user_id = st.session_state.get("user_id")
    if (is_admin or user_id) and st.session_state.resource_view == "add":
        if st.button("Back to Resources"):
            st.session_state.resource_view = "browse"
            st.rerun()

        form_title = "Add New Resource" if is_admin else "Suggest a Resource"
        st.markdown(f'<div class="section-title">{form_title}</div>', unsafe_allow_html=True)

        # A live, non-form URL field just for testing — fields inside st.form don't
        # update their Python value until the form is submitted, so a Test Link
        # button placed outside the form can't read a URL typed inside it.
        test_url_input = st.text_input(
            "Test a URL before adding (optional)",
            key="test_url_field",
            placeholder="Paste a URL here to test it, then copy it into the form below",
        )
        if st.button("Test Link", key="test_link_add"):
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
            new_page = st.text_input("Page Name", key="add_res_page")
            new_business = st.text_input("Business / Organization Name", key="add_res_business")
            new_description = st.text_area("Description", key="add_res_desc")
            new_category = st.text_input("Category (e.g. Government, URA, Partner)", key="add_res_cat")
            new_url = st.text_input("URL (e.g. Power BI embed link, website, etc.)", key="add_res_url")
            
            if is_admin:
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
            else:
                new_visible_all = True
                new_dept_ids = []
                new_admin_only = False
                
            submit_label = "Add Resource" if is_admin else "Submit Suggestion"
            submitted = st.form_submit_button(submit_label)

            if submitted:
                if not new_page or not new_business or not new_url:
                    st.error("Page Name, Business Name, and URL are required.")
                elif not new_visible_all and not new_dept_ids:
                    st.error("Select at least one department, or check 'Visible to everyone'.")
                else:
                    current_user = st.session_state.get("user_email", "admin@ura.go.ug")
                    dept_ids_to_save = [] if new_visible_all else new_dept_ids
                    resources_create(new_page, new_business, new_description, new_category, new_url, new_admin_only, dept_ids_to_save, current_user)
                    if is_admin:
                        st.success(f"Added '{new_business}'.")
                    else:
                        st.success(f"Suggested '{new_business}'. It will appear once approved by an admin.")
                    
                    # Clear form inputs manually
                    for k in ["add_res_page", "add_res_business", "add_res_desc", "add_res_cat", "add_res_url"]:
                        if k in st.session_state: del st.session_state[k]

                    st.cache_data.clear()
                    st.session_state.resource_view = "browse"
                    st.rerun()

        
        return

    # MAIN AREA — "Edit Resource" page
    if is_admin and st.session_state.resource_view == "edit":
        if st.button("Back to Resources"):
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
            edit_page = st.text_input("Page Name", value=row["page_name"], key="edit_res_page")
            edit_business = st.text_input("Business Name", value=row["business_name"], key="edit_res_business")
            edit_description = st.text_area("Description", value=row["description"] or "", key="edit_res_desc")
            edit_category = st.text_input("Category", value=row["category"] or "", key="edit_res_cat")
            edit_url = st.text_input("URL", value=row["url"], key="edit_res_url")
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
                save_clicked = st.form_submit_button("Save Changes", use_container_width=True)
            with col_delete:
                delete_clicked = st.form_submit_button("Delete", use_container_width=True)

            if save_clicked:
                if not edit_visible_all and not edit_dept_ids:
                    st.error("Select at least one department, or check 'Visible to everyone'.")
                else:
                    current_user = st.session_state.get("user_email", "admin@ura.go.ug")
                    dept_ids_to_save = [] if edit_visible_all else edit_dept_ids
                    resources_update(int(row["id"]), edit_page, edit_business, edit_description, edit_category, edit_url, edit_admin_only, dept_ids_to_save, current_user)
                    st.success("Updated.")
                    
                    for k in ["edit_res_page", "edit_res_business", "edit_res_desc", "edit_res_cat", "edit_res_url"]:
                        if k in st.session_state: del st.session_state[k]

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
        if st.button("Test Link", use_container_width=False):
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
        if st.session_state.get("user_id"): resources_record_recent(st.session_state.get("user_id"), resource_id)
        st.session_state.last_viewed_resource_id = resource_id

        log_event(
            st.session_state.get("user_email", "unknown"),
            "resource_view",
            resource_type="public_resource",
            resource_id=selected_name
        )

    added_rel = humanize_dt(selected_row.get("created_at"))
    updated_rel = humanize_dt(selected_row.get("updated_at"))


    col_title, col_fav = st.columns([5, 1])
    with col_title:
        st.markdown(f"### {html_lib.escape(str(selected_row['business_name']))}")
    with col_fav:
        if st.session_state.get("user_id"):
            _favs = resources_get_favorites(st.session_state.get("user_id"))
            _is_fav = resource_id in _favs
            _lbl = "Favorited" if _is_fav else "Favorite"
            if st.button(_lbl, key="fav_btn"):
                resources_toggle_favorite(st.session_state.get("user_id"), resource_id)
                st.rerun()

    if selected_row.get("description"):
        st.markdown(html_lib.escape(str(selected_row['description'])))

    meta_parts = [f"Added {added_rel}", f"Updated {updated_rel}"]
    if selected_row.get("category"):
        meta_parts.append(f"Category: {selected_row['category']}")
    _resource_depts = resource_department_access_get(resource_id)
    dept_label = ", ".join(_resource_depts) if _resource_depts else "All"
    meta_parts.append(f"Dept: {dept_label}")
    
    _status = selected_row.get("approval_status", "Approved")
    meta_parts.append(f"Status: {_status}")
    _sens = selected_row.get("sensitivity_classification", "Internal")
    meta_parts.append(f"Security: {_sens}")

    if is_admin and selected_row.get("admin_only"):
        meta_parts.append("Admin Only")
    st.caption(" • ".join(meta_parts))

    if is_admin and _status == "PendingApproval":
        if st.button("Approve Resource", type="primary"):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE public_resources SET approval_status = 'Approved' WHERE id = %s", (resource_id,))
            conn.commit()
            st.success("Resource approved!")
            st.rerun()


    # Admin-only detail card: view counts, timestamps, user metadata, audit log
    if is_admin:
        with st.expander("Admin Resource Stats & Audit Log", expanded=False):
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

    resource_url = str(selected_row.get("url", ""))
    if "youtube.com" in resource_url.lower() or "youtu.be" in resource_url.lower():
        st.video(resource_url)
    else:
        components.iframe(resource_url, height=600, scrolling=True)


def render_powerbi_reports():
    """Grouped nav bar built entirely from public_resources rows — no
    hardcoded pages or categories. Adding/editing/removing a report page
    is done through the same 'Add New Resource' form Public Resources
    already uses; any category name the admin types becomes its own
    nav group automatically."""

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
        if res_row.get("approval_status", "Approved") != "Approved":
            return False
        specific_depts = resource_dept_map.get(int(res_row["id"]), [])
        if not specific_depts:
            return True
        return bool(user_dept_access.intersection(specific_depts))

    mask = all_resources_df.apply(_resource_visible, axis=1)
    return all_resources_df[mask].reset_index(drop=True)