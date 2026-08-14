with open('views/public_resources.py', 'r') as f:
    content = f.read()

# Add Approval Status and Sensitivity to meta_parts
meta_insertion = """    _resource_depts = resource_department_access_get(resource_id)
    dept_label = ", ".join(_resource_depts) if _resource_depts else "All"
    meta_parts.append(f"🏢 Dept: {dept_label}")
    
    _status = selected_row.get("approval_status", "Approved")
    meta_parts.append(f"🚥 Status: {_status}")
    _sens = selected_row.get("sensitivity_classification", "Internal")
    meta_parts.append(f"🛡️ Security: {_sens}")
"""
content = content.replace(
    '    _resource_depts = resource_department_access_get(resource_id)\n    dept_label = ", ".join(_resource_depts) if _resource_depts else "All"\n    meta_parts.append(f"🏢 Dept: {dept_label}")',
    meta_insertion
)

# Add Approve button for admins if PendingApproval
approve_ui = """    st.caption(" • ".join(meta_parts))

    if is_admin and _status == "PendingApproval":
        if st.button("✅ Approve Resource", type="primary"):
            from core.db import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE public_resources SET approval_status = 'Approved' WHERE id = %s", (resource_id,))
            conn.commit()
            st.success("Resource approved!")
            st.rerun()
"""
content = content.replace('    st.caption(" • ".join(meta_parts))', approve_ui)

with open('views/public_resources.py', 'w') as f:
    f.write(content)
