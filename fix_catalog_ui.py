import re

with open('views/public_resources.py', 'r') as f:
    content = f.read()

# At line 55
insertion = """    if st.session_state.get("pr_view_mode") == "Full Catalog":
        st.markdown('<div class="section-title">Full Resource Catalog</div>', unsafe_allow_html=True)
        st.write("Browse all resources in the system. Resources with a 🔒 require special permissions to view.")
        
        # We use all_resources_df here so they see things they don't have access to
        for idx, row in all_resources_df.iterrows():
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
        
        return

"""

# Insert before "if resources_df.empty:"
content = content.replace(
    '    if resources_df.empty:\n        st.info("No resources match your visibility permissions or filters.")',
    insertion + '    if resources_df.empty:\n        st.info("No resources match your visibility permissions or filters.")'
)

with open('views/public_resources.py', 'w') as f:
    f.write(content)
