import ast

with open('core/db_users.py', 'r') as f:
    content = f.read()

# Replace SELECTs to join with roles
content = content.replace(
    "SELECT id, email, role, department, status, is_active, created_at FROM app_users",
    "SELECT u.id, u.email, r.name as role, u.department, u.status, u.is_active, u.created_at FROM app_users u LEFT JOIN roles r ON u.role_id = r.role_id"
)

content = content.replace(
    "SELECT id, email, requested_department, created_at FROM app_users",
    "SELECT u.id, u.email, u.requested_department, u.created_at FROM app_users u"
)

# Replace role string insertions with role_id logic
# For users_create:
# INSERT INTO app_users (email, password_hash, role, department, is_active, status)
content = content.replace(
    "INSERT INTO app_users (email, password_hash, role, department, is_active, status)",
    "INSERT INTO app_users (email, password_hash, role_id, department, is_active, status)"
)
content = content.replace(
    "(email, hashed, role, department, True, 'active')",
    "(email, hashed, 1 if role.lower() == 'admin' else 2, department, True, 'active')"
)

# For users_approve
content = content.replace(
    "UPDATE app_users SET status = 'active', is_active = TRUE, role = %s WHERE id = %s",
    "UPDATE app_users SET status = 'active', is_active = TRUE, role_id = (SELECT role_id FROM roles WHERE LOWER(name) = LOWER(%s)) WHERE id = %s"
)

# For users_update_role_department
content = content.replace(
    "UPDATE app_users SET role = %s WHERE id = %s",
    "UPDATE app_users SET role_id = (SELECT role_id FROM roles WHERE LOWER(name) = LOWER(%s)) WHERE id = %s"
)

# Admin count check
content = content.replace(
    "SELECT COUNT(*) FROM app_users WHERE role = 'admin' AND is_active = TRUE",
    "SELECT COUNT(*) FROM app_users u JOIN roles r ON u.role_id = r.role_id WHERE LOWER(r.name) = 'admin' AND u.is_active = TRUE"
)
content = content.replace(
    "SELECT role, is_active FROM app_users WHERE id = %s",
    "SELECT r.name as role, u.is_active FROM app_users u LEFT JOIN roles r ON u.role_id = r.role_id WHERE u.id = %s"
)

with open('core/db_users.py', 'w') as f:
    f.write(content)
