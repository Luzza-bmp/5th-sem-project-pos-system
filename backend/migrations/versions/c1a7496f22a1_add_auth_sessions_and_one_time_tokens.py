"""Add verification, password reset, access revocation and refresh sessions."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c1a7496f22a1"
down_revision: Union[str, Sequence[str], None] = "6917bb725011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table("auth_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_index("ix_auth_tokens_purpose", "auth_tokens", ["purpose"])
    op.create_table("auth_sessions",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("access_jti", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_access_jti", "auth_sessions", ["access_jti"])
    op.execute("""
        CREATE OR REPLACE FUNCTION public.auth_user_by_email(p_email varchar)
        RETURNS TABLE(id uuid, password_hash varchar, email_verified_at timestamptz)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO 'pg_catalog', 'public'
        AS $function$
            SELECT u.id, u.password_hash, u.email_verified_at
            FROM public.users AS u WHERE lower(u.email) = lower(p_email) LIMIT 1
        $function$;
    """)
    op.execute("ALTER FUNCTION public.auth_user_by_email(character varying) OWNER TO postgres")
    op.execute("REVOKE ALL ON FUNCTION public.auth_user_by_email(character varying) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION public.auth_user_by_email(character varying) TO pasaley_app")
    # Backend-only bookkeeping tables hold digests, never raw one-time credentials.
    for table in ("auth_tokens", "auth_sessions"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON TABLE public.{table} TO pasaley_app")
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY {table}_backend_access ON public.{table} FOR ALL TO pasaley_app USING (true) WITH CHECK (true)")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS public.auth_user_by_email(character varying)")
    for table in ("auth_sessions", "auth_tokens"):
        op.execute(f"DROP POLICY IF EXISTS {table}_backend_access ON public.{table}")
        op.drop_table(table)
    op.drop_column("users", "email_verified_at")
