with open('app.py', 'r') as f:
    content = f.read()

# Add a mode toggle before the search/pick row
insertion = """        if browsing:
            col_mode, col_resources, col_management = st.columns([1, 2, 1])
            with col_mode:
                with st.container(key="mode-card"):
                    st.markdown('<div class="ui-card-title">View Mode</div>', unsafe_allow_html=True)
                    view_mode = st.radio("Mode", ["Single Resource", "Full Catalog"], horizontal=True, key="pr_view_mode")
            
            with col_resources:
                if st.session_state.get("pr_view_mode") == "Single Resource":
"""
# Replace the original logic
content = content.replace(
    '        if browsing:\n            col_resources, col_management = st.columns([2, 1])\n\n            with col_resources:',
    insertion
)

# Indent the col_resources block
# Let's use re to do this safely.
import re
match = re.search(r'(with st\.container\(key="resources-card"\):.*?)(?=if is_admin:)', content, re.DOTALL)
if match:
    old_block = match.group(1)
    new_block = "\n".join(["    " + line if line.strip() else line for line in old_block.split("\n")])
    content = content.replace(old_block, new_block)

with open('app.py', 'w') as f:
    f.write(content)
