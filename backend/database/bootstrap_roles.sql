
-- Pasaley PostgreSQL role bootstrap
-- Run using the Supabase project database owner.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'pasaley_app'
    ) THEN
        CREATE ROLE pasaley_app LOGIN;
    END IF;
END
$$;
"""pasaley_app: a login identity used by the backend, with restricted permissions.

pasaley_provisioner: a non-login role intended to hold specific privileged permissions for provisioning stores."""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'pasaley_provisioner'
    ) THEN
        CREATE ROLE pasaley_provisioner;
    END IF;
END
$$;

-- 3. Enforce the intended security attributes.

ALTER ROLE pasaley_app
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    NOBYPASSRLS
    NOINHERIT;

ALTER ROLE pasaley_provisioner
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    NOBYPASSRLS
    INHERIT;
