# ---------------------------------------------------------------------------
# Uganda Revenue Authority (URA) Design System Tokens — Python side
#
# These MUST mirror assets/style.css exactly (:root block at the top of
# that file). style.css is the single source of truth for the visual
# identity; this file exists only so charts (st.line_chart, st.bar_chart,
# Plotly, etc.) that can't read CSS variables can still use the same
# colors. If you change a color in style.css, change it here too.
# ---------------------------------------------------------------------------

URA_NAVY = "#243F8D"
URA_NAVY_DARK = "#1A2E66"
URA_GOLD = "#FFF200"
URA_GOLD_SOFT = "#FFFBCC"
URA_TERRACOTTA = "#B54834"
URA_CANVAS = "#F6F3EC"
URA_SURFACE = "#FFFFFF"
URA_INK = "#1C2430"
URA_MUTED = "#6B7280"
URA_BORDER = "#E4DFD3"
URA_GREEN = "#1F7A4C"

# Backward-compatible aliases (old names some views/charts may still import).
# Prefer the URA_NAVY / URA_TERRACOTTA / etc. names above in new code —
# these exist only so nothing breaks while call sites get migrated.
URA_BLUE = URA_NAVY
URA_BLUE_DARK = URA_NAVY_DARK
URA_BLUE_LIGHT = URA_NAVY  # no separate "light blue" in the new palette
URA_BLUE_PALE = URA_CANVAS
URA_YELLOW = URA_GOLD
URA_YELLOW_DARK = "#E6D700"
URA_DARK = URA_INK
URA_TEXT_MUTED = URA_MUTED
URA_BG = URA_CANVAS

# Chart palette — ordered so the first color used is always institutional
# navy, matching every other primary-action element in the app.
PALETTE = [URA_NAVY, URA_GOLD, URA_TERRACOTTA, URA_GREEN, URA_MUTED]

# Tax-category color mapping, e.g. for st.bar_chart / Plotly category colors.
CATEGORY_COLOR_MAP = {
    "VAT": URA_NAVY,
    "EXCISE": URA_GOLD,
    "LOCAL_SERVICE": URA_TERRACOTTA,
    "WITHHOLDING": URA_GREEN,
}

SESSION_TIMEOUT_SECONDS = 1800