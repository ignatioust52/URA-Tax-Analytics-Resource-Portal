from datetime import datetime, timezone
import pandas as pd

def humanize_dt(dt):
    if dt is None or pd.isna(dt):
        return "—"
    if hasattr(dt, "to_pydatetime"):
        dt = dt.to_pydatetime()

    if getattr(dt, "tzinfo", None) is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

    seconds = (now - dt).total_seconds()
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return "just now"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} min ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hr ago"
    days = hours / 24
    if days < 30:
        return f"{int(days)} day(s) ago"
    months = days / 30
    if months < 12:
        return f"{int(months)} month(s) ago"
    return f"{int(months / 12)} year(s) ago"

import os, base64, streamlit as st
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "URA-logo.png")

@st.cache_data
def get_logo_base64():
    if not os.path.exists(LOGO_PATH):
        return None
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_logo_html(width, extra_style=""):
    """Returns an <img> tag for the logo, or '' if no logo file exists."""
    logo_b64 = get_logo_base64()
    if not logo_b64:
        return ""
    return f'<img src="data:image/png;base64,{logo_b64}" width="{width}" style="{extra_style}">'

