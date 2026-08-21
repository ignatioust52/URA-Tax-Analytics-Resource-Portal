import sys
import os
sys.path.append('/home/feza/ura-dashboard')
from core.db import get_connection
from core.auth import get_active_session

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT token FROM user_sessions us JOIN app_users u ON u.id = us.user_id WHERE u.email = 'officer@ura.go.ug' ORDER BY us.last_activity_at DESC LIMIT 1")
token = cur.fetchone()[0]

session = get_active_session(token)
print(session)
