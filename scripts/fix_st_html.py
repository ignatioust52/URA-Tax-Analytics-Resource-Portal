with open("core/auth.py", "r") as f:
    content = f.read()

# Replace st.markdown(left_html, unsafe_allow_html=True) with st.html(left_html)
content = content.replace("st.markdown(left_html, unsafe_allow_html=True)", "st.html(left_html)")
content = content.replace("st.markdown(right_header_html, unsafe_allow_html=True)", "st.html(right_header_html)")

with open("core/auth.py", "w") as f:
    f.write(content)

print("Replaced st.markdown with st.html")
