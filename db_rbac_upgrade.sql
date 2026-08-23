-- 1. Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    permission_key VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Insert core permissions
INSERT INTO permissions (permission_key, description) VALUES
('view_dashboard', 'View Dashboards'),
('view_kpis', 'View KPIs'),
('view_charts', 'View Charts'),
('view_raw_data', 'View Raw Data'),
('export_data', 'Export Data'),
('view_reports', 'View Reports'),
('create_reports', 'Create Reports'),
('export_reports', 'Export Reports'),
('view_resources', 'View Resources'),
('create_resources', 'Create Resources'),
('edit_resources', 'Edit Resources'),
('delete_resources', 'Delete Resources'),
('view_announcements', 'View Announcements'),
('create_announcements', 'Create Announcements'),
('edit_announcements', 'Edit Announcements'),
('delete_announcements', 'Delete Announcements'),
('view_users', 'View Users'),
('approve_users', 'Approve Users'),
('edit_users', 'Edit Users'),
('deactivate_users', 'Deactivate Users'),
('assign_roles', 'Assign Roles'),
('assign_departments', 'Assign Departments'),
('manage_roles', 'Manage Roles'),
('manage_departments', 'Manage Departments'),
('manage_permissions', 'Manage Permissions'),
('manage_system_settings', 'Manage System Settings'),
('view_audit_logs', 'View Audit Logs'),
('view_department_data', 'View Department Data'),
('view_all_data', 'View All Data'),
('manage_data', 'Manage Data')
ON CONFLICT (permission_key) DO NOTHING;

-- 2. Update Roles
-- Make sure the 8 standard roles exist
INSERT INTO roles (name, hierarchy_level, description) VALUES
('Super Administrator', 1, 'Full system access'),
('System Administrator', 2, 'Technical/system administration access'),
('Department Administrator', 3, 'Can manage users and content within their approved department scope'),
('Manager', 4, 'Primarily views department dashboards, reports, and content'),
('Senior Analyst', 5, 'Advanced analytical access'),
('Analyst', 6, 'View permitted datasets, analyze data, generate reports'),
('Officer', 7, 'Operational access to permitted department information'),
('Viewer', 8, 'Read-only access to permitted information')
ON CONFLICT (name) DO NOTHING;

-- 3. Role Permissions Mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Assign ALL permissions to Super Administrator (Role Level 1)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.id FROM roles r, permissions p WHERE r.name = 'Super Administrator'
ON CONFLICT DO NOTHING;

-- Map old Admin users to Super Administrator
UPDATE app_users SET role_id = (SELECT role_id FROM roles WHERE name = 'Super Administrator') WHERE role_id = (SELECT role_id FROM roles WHERE name = 'Admin');
UPDATE app_users SET role = 'super administrator' WHERE role = 'admin';

-- 4. Departments
-- Insert official departments
INSERT INTO departments (name) VALUES
('Domestic Taxes Department'),
('Customs Department'),
('Tax Investigations Department'),
('Legal Services & Board Affairs'),
('Finance Department'),
('Human Resources & Development'),
('Information Technology (IT/Digital)'),
('Internal Audit'),
('Public and Corporate Affairs'),
('Research, Policy Analysis & Planning'),
('Commissioner General''s Office / Executive Management'),
('Taxpayer Services / Client Service'),
('Enforcement / Compliance'),
('Corporate Services / Administration'),
('Internal Affairs / Risk Management')
ON CONFLICT (name) DO NOTHING;

-- 5. Visibility updates
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='public_resources' AND column_name='visibility') THEN
        ALTER TABLE public_resources ADD COLUMN visibility VARCHAR(30) NOT NULL DEFAULT 'EVERYONE';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='announcements' AND column_name='visibility') THEN
        ALTER TABLE announcements ADD COLUMN visibility VARCHAR(30) NOT NULL DEFAULT 'EVERYONE';
    END IF;
END $$;

-- 6. Announcements Department Access
CREATE TABLE IF NOT EXISTS announcement_department_access (
    announcement_id INTEGER REFERENCES announcements(announcement_id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    PRIMARY KEY (announcement_id, department_id)
);

-- Migrate old audience_department_id to announcement_department_access
INSERT INTO announcement_department_access (announcement_id, department_id)
SELECT announcement_id, audience_department_id FROM announcements WHERE audience_department_id IS NOT NULL
ON CONFLICT DO NOTHING;

-- Update announcements visibility based on audience_department_id
UPDATE announcements SET visibility = 'SELECTED_DEPARTMENTS' WHERE audience_department_id IS NOT NULL;

-- 7. Add active_department_id to user_sessions (Wait, user_sessions doesn't have it natively, usually JWT stores it, but let's add it if user_sessions is DB backed)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='user_sessions' AND column_name='active_department_id') THEN
            ALTER TABLE user_sessions ADD COLUMN active_department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL;
        END IF;
    END IF;
END $$;
