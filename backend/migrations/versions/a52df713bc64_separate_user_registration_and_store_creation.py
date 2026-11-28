"""Separate user registration from authenticated store creation."""
from typing import Sequence, Union
from alembic import op

revision: str = "a52df713bc64"
down_revision: Union[str, Sequence[str], None] = "ed42c17a9b30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Narrow SECURITY DEFINER function: the app can register a user without
    # giving its runtime role broad INSERT access to the users table.
    op.execute("""
        CREATE FUNCTION public.auth_register_user(
            p_email varchar, p_password_hash varchar
        ) RETURNS uuid
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
        DECLARE v_user_id uuid;
        BEGIN
            v_user_id := gen_random_uuid();
            INSERT INTO public.users (id, email, password_hash)
            VALUES (v_user_id, lower(p_email), p_password_hash);
            RETURN v_user_id;
        END;
        $function$;
    """)
    op.execute("ALTER FUNCTION public.auth_register_user(character varying, character varying) OWNER TO postgres")
    op.execute("REVOKE ALL ON FUNCTION public.auth_register_user(character varying, character varying) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.auth_register_user(character varying, character varying) TO pasaley_app")

    # The function checks the transaction-local JWT identity before creating
    # both records, so callers cannot create an owner membership for someone else.
    op.execute("""
        CREATE FUNCTION public.provision_store_for_user(
            p_user_id uuid, p_store_name varchar, p_store_address text DEFAULT NULL
        ) RETURNS TABLE(created_store_id uuid)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
        DECLARE v_store_id uuid;
        BEGIN
            IF p_user_id IS DISTINCT FROM public.current_app_user_id() THEN
                RAISE EXCEPTION 'store owner must match authenticated user'
                    USING ERRCODE = '42501';
            END IF;
            v_store_id := gen_random_uuid();
            INSERT INTO public.stores (id, name, address)
            VALUES (v_store_id, p_store_name, p_store_address);
            INSERT INTO public.members (id, user_id, store_id, role, status)
            VALUES (gen_random_uuid(), p_user_id, v_store_id, 'owner', 'active');
            RETURN QUERY SELECT v_store_id;
        END;
        $function$;
    """)
    op.execute("ALTER FUNCTION public.provision_store_for_user(uuid, character varying, text) OWNER TO postgres")
    op.execute("REVOKE ALL ON FUNCTION public.provision_store_for_user(uuid, character varying, text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.provision_store_for_user(uuid, character varying, text) TO pasaley_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS public.provision_store_for_user(uuid, character varying, text)")
    op.execute("DROP FUNCTION IF EXISTS public.auth_register_user(character varying, character varying)")
