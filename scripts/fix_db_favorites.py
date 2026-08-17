with open('core/db_resources.py', 'r') as f:
    content = f.read()

funcs = """
def resources_toggle_favorite(user_id, resource_id):
    conn = get_connection()
    cur = conn.cursor()
    # Check if exists
    cur.execute("SELECT 1 FROM public_resource_favorites WHERE user_id = %s AND resource_id = %s", (int(user_id), int(resource_id)))
    exists = cur.fetchone()
    if exists:
        cur.execute("DELETE FROM public_resource_favorites WHERE user_id = %s AND resource_id = %s", (int(user_id), int(resource_id)))
        is_fav = False
    else:
        cur.execute("INSERT INTO public_resource_favorites (user_id, resource_id) VALUES (%s, %s)", (int(user_id), int(resource_id)))
        is_fav = True
    conn.commit()
    cur.close()
    return is_fav

def resources_get_favorites(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT resource_id FROM public_resource_favorites WHERE user_id = %s", (int(user_id),))
    favs = [r[0] for r in cur.fetchall()]
    cur.close()
    return favs

def resources_record_recent(user_id, resource_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        \"\"\"
        INSERT INTO public_resource_recent (user_id, resource_id, viewed_at)
        VALUES (%s, %s, now())
        ON CONFLICT (user_id, resource_id, viewed_at) DO NOTHING
        \"\"\",
        (int(user_id), int(resource_id))
    )
    conn.commit()
    cur.close()

def resources_get_recent(user_id, limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        \"\"\"
        SELECT resource_id FROM public_resource_recent 
        WHERE user_id = %s 
        ORDER BY viewed_at DESC LIMIT %s
        \"\"\",
        (int(user_id), int(limit))
    )
    recents = []
    seen = set()
    for row in cur.fetchall():
        r_id = row[0]
        if r_id not in seen:
            seen.add(r_id)
            recents.append(r_id)
    cur.close()
    return recents
"""

content = content + "\n\n" + funcs

with open('core/db_resources.py', 'w') as f:
    f.write(content)
