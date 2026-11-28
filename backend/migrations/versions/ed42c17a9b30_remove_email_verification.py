"""Remove the temporarily deferred email-verification feature."""
from typing import Sequence, Union
from alembic import op

revision: str = "ed42c17a9b30"
down_revision: Union[str, Sequence[str], None] = "c1a7496f22a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL cannot change a function's returned columns with CREATE OR REPLACE.
    op.execute("DROP FUNCTION IF EXISTS public.auth_user_by_email(character varying)")
    op.execute("ALTER TABLE public.users DROP COLUMN IF EXISTS email_verified_at")
    op.execute("""
        CREATE FUNCTION public.auth_user_by_email(p_email varchar)
        RETURNS TABLE(id uuid, password_hash varchar)
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
            SELECT u.id, u.password_hash
            FROM public.users AS u WHERE lower(u.email) = lower(p_email) LIMIT 1
        $function$;
    """)
    op.execute("ALTER FUNCTION public.auth_user_by_email(character varying) OWNER TO postgres")
    op.execute("REVOKE ALL ON FUNCTION public.auth_user_by_email(character varying) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.auth_user_by_email(character varying) TO pasaley_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS public.auth_user_by_email(character varying)")
    op.execute("ALTER TABLE public.users ADD COLUMN email_verified_at timestamptz")
    op.execute("""
        CREATE FUNCTION public.auth_user_by_email(p_email varchar)
        RETURNS TABLE(id uuid, password_hash varchar, email_verified_at timestamptz)
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
            SELECT u.id, u.password_hash, u.email_verified_at
            FROM public.users AS u WHERE lower(u.email) = lower(p_email) LIMIT 1
        $function$;
    """)
    op.execute("ALTER FUNCTION public.auth_user_by_email(character varying) OWNER TO postgres")
    op.execute("REVOKE ALL ON FUNCTION public.auth_user_by_email(character varying) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.auth_user_by_email(character varying) TO pasaley_app")
