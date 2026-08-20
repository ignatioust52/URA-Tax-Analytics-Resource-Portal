import streamlit as st
import pandas as pd
from core.db_resources import resources_get_all, resources_update_approval

def render_governance():
    st.markdown('<div class="section-title">Governance Queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Review and approve dashboards and resources pending publication.</div>',
        unsafe_allow_html=True,
    )

    is_admin = st.session_state.get("role") == "admin"
    if not is_admin:
        st.warning("Access restricted to administrators.")
        return

    df = resources_get_all()
    if not df.empty and "approval_status" in df.columns:
        pending_df = df[df["approval_status"] == "PendingApproval"]
    else:
        pending_df = pd.DataFrame()

    if pending_df.empty:
        st.info("🎉 No resources pending approval.")
        return

    st.write(f"**{len(pending_df)} resource(s) awaiting your review.**")

    for _, row in pending_df.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {row['business_name']}")
                st.write(f"**Category:** {row['category']} | **Department:** {row['department']}")
                st.write(f"**Description:** {row['description']}")
                st.write(f"**Requested by:** {row['added_by']}")

            with col2:
                st.write("")
                st.write("")
                if st.button("Approve", key=f"approve_{row['id']}", type="primary"):
                    resources_update_approval(row['id'], "Approved", st.session_state.get("user_id", None))
                    st.success(f"Approved {row['business_name']}")
                    st.rerun()
                
                if st.button("Reject", key=f"reject_{row['id']}"):
                    resources_update_approval(row['id'], "Rejected", st.session_state.get("user_id", None))
                    st.warning(f"Rejected {row['business_name']}")
                    st.rerun()
