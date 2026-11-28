DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'pasaley_app'
    ) THEN
        CREATE ROLE pasaley_app LOGIN;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'pasaley_provisioner'
    ) THEN
        CREATE ROLE pasaley_provisioner;
    END IF;
END
$$;