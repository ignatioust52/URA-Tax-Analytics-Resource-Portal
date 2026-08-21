#!/usr/bin/env python3
import sys
import os
import bcrypt

# Add the parent directory to sys.path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import get_connection

def seed_admin(email, password):
    print(f"Attempting to seed admin: {email}")
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Ensure the "admin" role exists
    cur.execute("SELECT role_id FROM roles WHERE LOWER(name) = 'admin'")
    role_row = cur.fetchone()
    if not role_row:
        print("Creating 'admin' role...")
        cur.execute("INSERT INTO roles (name, hierarchy_level) VALUES ('admin', 100) RETURNING role_id")
        role_id = cur.fetchone()[0]
    else:
        role_id = role_row[0]
        
    # 2. Check if user already exists
    cur.execute("SELECT id FROM app_users WHERE LOWER(email) = LOWER(%s)", (email,))
    if cur.fetchone():
        print(f"Error: User {email} already exists!")
        sys.exit(1)
        
    # 3. Create the admin user
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute(
        """
        INSERT INTO app_users (email, password_hash, role_id, department, is_active, status)
        VALUES (%s, %s, %s, 'IT/System Admin', TRUE, 'active')
        RETURNING id
        """,
        (email.lower().strip(), hashed, role_id)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    print(f"Success! Admin user created with ID: {new_id}")
    print(f"You can now log in with {email} and the provided password.")

if __name__ == "__main__":
    print("=== URA Dashboard - First Admin Bootstrapper ===")
    email = input("Enter admin email (e.g. admin@ura.go.ug): ").strip()
    if not email:
        print("Email is required.")
        sys.exit(1)
        
    password = input("Enter secure password: ").strip()
    if not password:
        print("Password is required.")
        sys.exit(1)
        
    seed_admin(email, password)
