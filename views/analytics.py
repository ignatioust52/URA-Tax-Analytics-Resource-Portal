import streamlit as st
import pandas as pd
from core.db_audit import get_audit_log


def render_analytics():
    is_admin = st.session_state.get("role") == "admin"
    if not is_admin:
        st.warning("Access restricted to administrators.")
        return

    st.markdown('<div class="section-title">Admin Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Resource-view activity across the Public Resources catalog.</div>',
        unsafe_allow_html=True,
    )

    audit_df = get_audit_log(limit=5000)

    if audit_df.empty:
        st.info("No audit logs available to display analytics.")
        return

    # Convert logged_at to datetime
    audit_df["logged_at"] = pd.to_datetime(audit_df["logged_at"])

    # Filter only resource_view actions
    views_df = audit_df[audit_df["action"] == "resource_view"]

    # Filter out views for resources that have been deleted
    from core.db_resources import resources_get_all
    active_resources_df = resources_get_all()
    active_names = active_resources_df["business_name"].tolist() if not active_resources_df.empty else []
    views_df = views_df[views_df["resource_id"].isin(active_names)]

    if views_df.empty:
        st.info("No resource view logs available yet.")
        return

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Total Recorded Views", len(views_df))
    with kpi2:
        unique_users = len(views_df["user_email"].unique())
        st.metric("Unique Viewers", unique_users)
    with kpi3:
        unique_resources = len(views_df["resource_id"].unique())
        st.metric("Unique Resources Viewed", unique_resources)

    st.markdown("<div style='margin: 1.25rem 0;'></div>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        with st.container(border=True):
            st.markdown('<div class="ui-card-title">Daily Views Trend</div>', unsafe_allow_html=True)
            views_by_date = views_df.copy()
            views_by_date["date"] = views_by_date["logged_at"].dt.date
            daily_views = views_by_date.groupby("date").size().reset_index(name="views")
            st.line_chart(
                daily_views, x="date", y="views", use_container_width=True, color="#243F8D"
            )

    with col_chart2:
        with st.container(border=True):
            st.markdown('<div class="ui-card-title">Top 10 Most Popular Resources</div>', unsafe_allow_html=True)
            popular = (
                views_df.groupby("resource_id").size().reset_index(name="views")
                .sort_values("views", ascending=False).head(10)
            )
            st.bar_chart(
                popular, x="resource_id", y="views", use_container_width=True, color="#B54834"
            )

    st.markdown("<div style='margin: 1.25rem 0;'></div>", unsafe_allow_html=True)
    with st.expander("🔍 View Detailed Activity Log Data Table"):
        st.dataframe(audit_df, use_container_width=True)