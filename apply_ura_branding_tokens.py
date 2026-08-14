import re

# 1. Update .streamlit/config.toml
config_content = """# URA Corporate Theme

[theme]
base = "light"
primaryColor = "#003366"             # Primary Institutional Blue
backgroundColor = "#F8FAFC"          # Canvas Background
secondaryBackgroundColor = "#FFFFFF" # Surface Cards
textColor = "#334155"                # Legible Dark Gray Body Text
font = "sans serif"

[client]
toolbarMode = "minimal"
"""

with open(".streamlit/config.toml", "w") as f:
    f.write(config_content)

print("Updated config.toml")

# 2. Update assets/style.css
css_content = """/* ---------------------------------------------------------------------------
UGANDA REVENUE AUTHORITY (URA) — OFFICIAL BRAND IDENTITY STYLESHEET
Design Tokens:
- Primary Institutional Blue: #003366
- Accent Gold/Yellow: #FFC72C
- Success Tax Green: #008751
- Canvas Background: #F8FAFC
- Surface Cards: #FFFFFF
- Headings: #0F172A (Weight 700)
- Body/Labels: #334155 (Weight 400)
- Micro Radius: 6px - 8px
--------------------------------------------------------------------------- */

/* Hide default Streamlit clutter */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Base App Layout & Canvas */
.stApp {
    background-color: #F8FAFC !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6, .section-title {
    color: #0F172A !important;
    font-weight: 700 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

p, label, span, div {
    color: #334155;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Surface Cards & Grid Menus */
[data-testid="stVerticalBlockBorderWrapper"], .ura-grid-card {
    background: #FFFFFF !important;
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05) !important;
    transition: all 0.2s ease-in-out;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover, .ura-grid-card:hover {
    box-shadow: 0 4px 12px -2px rgba(0, 51, 102, 0.12) !important;
    transform: translateY(-2px);
    border-color: #003366 !important;
}

/* Primary Action Buttons */
button[kind="primary"],
div[data-testid="stForm"] button[type="submit"] {
    background-color: #003366 !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    border: none !important;
    height: 46px !important;
    transition: all 0.2s ease-in-out !important;
}
button[kind="primary"]:hover,
div[data-testid="stForm"] button[type="submit"]:hover {
    background-color: #002244 !important;
    box-shadow: 0 4px 12px rgba(0, 51, 102, 0.25) !important;
}

/* Secondary Buttons */
button[kind="secondary"] {
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    color: #003366 !important;
    font-weight: 600 !important;
    height: 46px !important;
}
button[kind="secondary"]:hover {
    background-color: #F1F5F9 !important;
}

/* Accent Gold Buttons */
.btn-gold button {
    background-color: #FFC72C !important;
    color: #0F172A !important;
    border-color: #E6B327 !important;
    font-weight: 700 !important;
}
.btn-gold button:hover {
    background-color: #E6B327 !important;
}

/* Status Chips & Badges */
.ura-chip-success {
    background-color: #E6F3EB;
    color: #008751;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}
.ura-chip-warning {
    background-color: #FFF9E6;
    color: #0F172A;
    border: 1px solid #FFC72C;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Floating URA-Bubbles Panel */
.ura-bubbles-container {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    z-index: 9999;
}
.ura-bubble {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background-color: #003366;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 51, 102, 0.25);
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    text-decoration: none;
    font-size: 1.25rem;
    position: relative;
}
.ura-bubble:hover {
    background-color: #FFC72C;
    color: #003366;
    transform: scale(1.1);
}
.ura-bubble .tooltip {
    visibility: hidden;
    background-color: #0F172A;
    color: #FFFFFF;
    text-align: center;
    border-radius: 6px;
    padding: 6px 10px;
    position: absolute;
    right: 62px;
    z-index: 1;
    opacity: 0;
    transition: opacity 0.2s;
    white-space: nowrap;
    font-size: 0.85rem;
    font-weight: 500;
}
.ura-bubble:hover .tooltip {
    visibility: visible;
    opacity: 1;
}

/* Input Fields Styling */
div[data-baseweb="input"] {
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    height: 46px !important;
    transition: all 0.2s ease;
}
div[data-baseweb="input"]:focus-within {
    border-color: #003366 !important;
    box-shadow: 0 0 0 3px rgba(0, 51, 102, 0.12) !important;
}
div[data-baseweb="input"] input {
    color: #0F172A !important;
    font-size: 0.925rem !important;
}

/* Selectbox Styling */
div[data-baseweb="select"] > div {
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    height: 46px !important;
}

/* Left Pane Split Login */
.login-left-pane {
    background: linear-gradient(145deg, #002244 0%, #003366 65%, #001A33 100%);
    width: 100%;
    min-height: 85vh;
    border-radius: 16px;
    padding: 3rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    box-shadow: 0 12px 32px rgba(0, 51, 102, 0.2);
}

.login-brand-title span {
    color: #FFC72C;
}

/* Tab Header Styling */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 12px !important;
    border-bottom: 2px solid #E2E8F0 !important;
    margin-bottom: 1.25rem !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    height: 40px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #64748B !important;
    padding: 0 16px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #003366 !important;
    border-bottom-color: #003366 !important;
}

.login-card-header-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #003366;
    margin-top: 10px;
    letter-spacing: 0.5px;
}
.login-card-header-title span {
    color: #FFC72C;
}
"""

with open("assets/style.css", "w") as f:
    f.write(css_content)

print("Updated style.css with official URA design tokens")
