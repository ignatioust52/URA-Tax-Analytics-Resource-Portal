with open('views/public_resources.py', 'r') as f:
    content = f.read()

# Replace the Full Catalog loop with a grid layout
old_catalog = """        for idx, row in all_resources_df.iterrows():
            has_access = row["id"] in resources_df["id"].values
            icon = "✅" if has_access else "🔒"
            
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1])
                with col_info:
                    st.markdown(f"#### {icon} {html_lib.escape(str(row['business_name']))}")
                    if row.get('description'):
                        st.caption(html_lib.escape(str(row['description'])))
                    st.caption(f"Category: {row.get('category', 'Uncategorized')} | Status: {row.get('approval_status', 'Approved')}")
                
                with col_action:
                    if has_access:
                        if st.button("View", key=f"cat_view_{row['id']}"):
                            st.session_state["pr_view_mode"] = "Single Resource"
                            st.session_state["pr_resource_select"] = row["business_name"]
                            st.rerun()
                    else:
                        if st.button("Request Access", key=f"cat_req_{row['id']}"):
                            st.toast(f"Access request sent for {row['business_name']}!")
"""

new_catalog = """        st.markdown('<div class="section-title">URA Quick Services Grid</div>', unsafe_allow_html=True)
        
        # Grid Layout (3 columns)
        cols_per_row = 3
        for i in range(0, len(all_resources_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(all_resources_df):
                    row = all_resources_df.iloc[i + j]
                    has_access = row["id"] in resources_df["id"].values
                    icon = "✅" if has_access else "🔒"
                    
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"### {icon}")
                            st.markdown(f"**{html_lib.escape(str(row['business_name']))}**")
                            if row.get('description'):
                                st.caption(html_lib.escape(str(row['description'])))
                            
                            st.markdown("<br>", unsafe_allow_html=True) # spacer
                            
                            if has_access:
                                if st.button("View", key=f"cat_view_{row['id']}", use_container_width=True, type="primary"):
                                    st.session_state["pr_view_mode"] = "Single Resource"
                                    st.session_state["pr_resource_select"] = row["business_name"]
                                    st.rerun()
                            else:
                                if st.button("Request Access", key=f"cat_req_{row['id']}", use_container_width=True):
                                    st.toast(f"Access request sent for {row['business_name']}!")
"""

content = content.replace(old_catalog, new_catalog)

# Also remove the previous title since new_catalog adds it
content = content.replace(
    '        st.markdown(\'<div class="section-title">Full Resource Catalog</div>\', unsafe_allow_html=True)\n        st.write("Browse all resources in the system. Resources with a 🔒 require special permissions to view.")',
    ''
)

# Add the Bubbles at the very end of render_public_resources
bubbles = """
    # --- URA-BUBBLES FLOATING PANEL ---
    st.markdown(
        \"\"\"
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
        \"\"\",
        unsafe_allow_html=True
    )
"""

content = content.replace("    if is_admin and st.session_state.resource_view == \"add\":", bubbles + "\n    if is_admin and st.session_state.resource_view == \"add\":")

with open('views/public_resources.py', 'w') as f:
    f.write(content)
