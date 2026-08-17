with open('views/public_resources.py', 'r') as f:
    content = f.read()

# Fix recent view recording
content = content.replace(
    '        resources_record_recent(st.session_state.get("user_id", 0), resource_id)',
    '        if st.session_state.get("user_id"): resources_record_recent(st.session_state.get("user_id"), resource_id)'
)

# Fix favorite button
fav_btn_bad = """        from core.db_resources import resources_toggle_favorite, resources_get_favorites
        _favs = resources_get_favorites(st.session_state.get("user_id", 0))
        _is_fav = resource_id in _favs
        _lbl = "🌟 Favorited" if _is_fav else "⭐ Favorite"
        if st.button(_lbl, key="fav_btn"):
            resources_toggle_favorite(st.session_state.get("user_id", 0), resource_id)
            st.rerun()"""
fav_btn_good = """        if st.session_state.get("user_id"):
            from core.db_resources import resources_toggle_favorite, resources_get_favorites
            _favs = resources_get_favorites(st.session_state.get("user_id"))
            _is_fav = resource_id in _favs
            _lbl = "🌟 Favorited" if _is_fav else "⭐ Favorite"
            if st.button(_lbl, key="fav_btn"):
                resources_toggle_favorite(st.session_state.get("user_id"), resource_id)
                st.rerun()"""
content = content.replace(fav_btn_bad, fav_btn_good)

with open('views/public_resources.py', 'w') as f:
    f.write(content)
