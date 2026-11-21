
-- Pasaley PostgreSQL role bootstrap
-- Run using the Supabase project database owner.

-- 1. Create the application runtime role if it doesn't exist.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'pasaley_app'
    ) THEN
        CREATE ROLE pasaley_app;
    END IF;
END
$$;

-- 2. Create the store provisioning role if it doesn't exist.
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
