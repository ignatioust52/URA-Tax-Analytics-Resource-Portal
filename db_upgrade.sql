CREATE TABLE IF NOT EXISTS roles (
    role_id          SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL UNIQUE,
    hierarchy_level  INTEGER NOT NULL,
    description      TEXT
);

-- Insert default roles (if not exists)
INSERT INTO roles (name, hierarchy_level, description) VALUES
('Admin', 1, 'Full system access'),
('Viewer', 10, 'General viewer access')
ON CONFLICT (name) DO NOTHING;

-- Add role_id to app_users if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='app_users' AND column_name='role_id') THEN
        ALTER TABLE app_users ADD COLUMN role_id INTEGER REFERENCES roles(role_id);
    END IF;
END $$;

-- Migrate existing roles
UPDATE app_users SET role_id = (SELECT role_id FROM roles WHERE name = 'Admin') WHERE role = 'admin' AND role_id IS NULL;
UPDATE app_users SET role_id = (SELECT role_id FROM roles WHERE name = 'Viewer') WHERE (role = 'viewer' OR role IS NULL) AND role_id IS NULL;

-- We could drop the old role column, but let's keep it for a moment just in case, or drop it
-- ALTER TABLE app_users DROP COLUMN role;

CREATE TABLE IF NOT EXISTS user_special_permissions (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES app_users(id),
    permission_key   VARCHAR(100) NOT NULL,
    granted_by       INTEGER REFERENCES app_users(id),
    reason           TEXT,
    expires_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public_resource_favorites (
    user_id       INTEGER REFERENCES app_users(id),
    resource_id   INTEGER REFERENCES public_resources(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, resource_id)
);

CREATE TABLE IF NOT EXISTS public_resource_recent (
    user_id       INTEGER REFERENCES app_users(id),
    resource_id   INTEGER REFERENCES public_resources(id),
    viewed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, resource_id, viewed_at)
);

CREATE TABLE IF NOT EXISTS role_resource_access (
    role_id       INTEGER REFERENCES roles(role_id),
    resource_id   INTEGER REFERENCES public_resources(id),
    can_view      BOOLEAN NOT NULL DEFAULT TRUE,
    can_edit      BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (role_id, resource_id)
);

CREATE TABLE IF NOT EXISTS public_resource_lifecycle_events (
    event_id       SERIAL PRIMARY KEY,
    resource_id    INTEGER NOT NULL REFERENCES public_resources(id),
    stage          VARCHAR(30) NOT NULL,
    actor_user_id  INTEGER REFERENCES app_users(id),
    notes          TEXT,
    occurred_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add governance fields to public_resources
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='public_resources' AND column_name='approval_status') THEN
        ALTER TABLE public_resources ADD COLUMN approval_status VARCHAR(30) NOT NULL DEFAULT 'Approved';
        ALTER TABLE public_resources ADD COLUMN sensitivity_classification VARCHAR(30) NOT NULL DEFAULT 'Internal';
    END IF;
END $$;
