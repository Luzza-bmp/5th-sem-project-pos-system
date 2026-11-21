
"""Add database security and RLS policies.

Revision ID: 6917bb725011
Revises: 8a594b869d5b
"""

from typing import Sequence, Union

from alembic import op


revision: str = "6917bb725011"
down_revision: Union[str, Sequence[str], None] = "8a594b869d5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Install Pasaley database security."""

    # 1. Schema access
    op.execute("GRANT USAGE ON SCHEMA public TO pasaley_app")
    op.execute("GRANT USAGE ON SCHEMA public TO pasaley_provisioner")

    # 2. Table privileges for the application role
    app_permissions = {
        "users": "SELECT, INSERT, UPDATE",
        "stores": "SELECT, UPDATE",
        "members": "SELECT",
        "invites": "SELECT, INSERT, UPDATE",
        "invoices": "SELECT, INSERT, UPDATE",
        "products": "SELECT, INSERT, UPDATE",
        "restock_batches": "SELECT, INSERT, UPDATE",
        "restock_lines": "SELECT, INSERT, UPDATE",
        "items": "SELECT, INSERT, UPDATE",
        "payments": "SELECT, INSERT, UPDATE",
        "stock_movements": "SELECT, INSERT, UPDATE",
    }

    for table, permissions in app_permissions.items():
        op.execute(
            f"GRANT {permissions} ON TABLE public.{table} TO pasaley_app"
        )

    # The provisioner only needs to insert the initial records.
    for table in ("users", "stores", "members"):
        op.execute(
            f"GRANT INSERT ON TABLE public.{table} TO pasaley_provisioner"
        )

    # 3. Application identity function
    op.execute("""
        CREATE OR REPLACE FUNCTION public.current_app_user_id()
        RETURNS uuid
        LANGUAGE sql
        STABLE
        AS $function$
            SELECT NULLIF(
                current_setting('app.current_user_id', true),
                ''
            )::uuid;
        $function$;
    """)

    # 4. Store role-checking function
    op.execute("""
        CREATE OR REPLACE FUNCTION public.has_store_role(
            target_store_id uuid,
            allowed_roles text[]
        )
        RETURNS boolean
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
            SELECT EXISTS (
                SELECT 1
                FROM public.members AS m
                WHERE m.store_id = target_store_id
                  AND m.user_id = public.current_app_user_id()
                  AND m.status = 'active'
                  AND m.role = ANY(allowed_roles)
            );
        $function$;
    """)

    # 5. Active membership-checking function
    op.execute("""
        CREATE OR REPLACE FUNCTION public.is_active_store_member(
            target_store_id uuid
        )
        RETURNS boolean
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
            SELECT EXISTS (
                SELECT 1
                FROM public.members AS m
                WHERE m.store_id = target_store_id
                  AND m.user_id = public.current_app_user_id()
                  AND m.status = 'active'
            );
        $function$;
    """)

    # 6. Initial store provisioning function
    op.execute("""
        CREATE OR REPLACE FUNCTION public.provision_initial_store(
            p_email varchar,
            p_password_hash varchar,
            p_store_name varchar,
            p_store_address text DEFAULT NULL
        )
        RETURNS TABLE (
            created_user_id uuid,
            created_store_id uuid,
            created_member_id uuid
        )
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path TO 'pg_catalog', 'public'
        AS $function$
        DECLARE
            v_user_id uuid;
            v_store_id uuid;
            v_member_id uuid;
        BEGIN
            v_user_id := pg_catalog.gen_random_uuid();

            INSERT INTO public.users (
                id, email, password_hash
            )
            VALUES (
                v_user_id, p_email, p_password_hash
            );

            v_store_id := pg_catalog.gen_random_uuid();

            INSERT INTO public.stores (
                id, name, address
            )
            VALUES (
                v_store_id, p_store_name, p_store_address
            );

            v_member_id := pg_catalog.gen_random_uuid();

            INSERT INTO public.members (
                id, user_id, store_id, role, status
            )
            VALUES (
                v_member_id,
                v_user_id,
                v_store_id,
                'owner',
                'active'
            );

            RETURN QUERY
            SELECT v_user_id, v_store_id, v_member_id;
        END;
        $function$;
    """)

    # 7. Assign the intended function owners.
    op.execute(
        "ALTER FUNCTION public.current_app_user_id() OWNER TO postgres"
    )
    op.execute(
        "ALTER FUNCTION public.has_store_role(uuid, text[]) OWNER TO postgres"
    )
    op.execute(
        "ALTER FUNCTION public.is_active_store_member(uuid) OWNER TO postgres"
    )
    op.execute("""
        ALTER FUNCTION public.provision_initial_store(
            character varying,
            character varying,
            character varying,
            text
        ) OWNER TO pasaley_provisioner
    """)
    # Remove PostgreSQL's default PUBLIC function execution access.
    op.execute("""
        REVOKE ALL ON FUNCTION public.current_app_user_id()
        FROM PUBLIC
    """)
    op.execute("""
        REVOKE ALL ON FUNCTION public.has_store_role(uuid, text[])
        FROM PUBLIC
    """)
    op.execute("""
        REVOKE ALL ON FUNCTION public.is_active_store_member(uuid)
        FROM PUBLIC
    """)
    op.execute("""
        REVOKE ALL ON FUNCTION public.provision_initial_store(
            character varying,
            character varying,
            character varying,
            text
        ) FROM PUBLIC
    """)
    op.execute("""
        REVOKE ALL ON FUNCTION public.rls_auto_enable()
        FROM PUBLIC
    """)
    # 8. Function execution permissions.
    op.execute("""
        GRANT EXECUTE ON FUNCTION public.current_app_user_id()
        TO pasaley_app
    """)
    op.execute("""
        GRANT EXECUTE ON FUNCTION public.has_store_role(uuid, text[])
        TO pasaley_app
    """)
    op.execute("""
        GRANT EXECUTE ON FUNCTION public.is_active_store_member(uuid)
        TO pasaley_app
    """)
    op.execute("""
        GRANT EXECUTE ON FUNCTION public.provision_initial_store(
            character varying,
            character varying,
            character varying,
            text
        ) TO pasaley_app, pasaley_provisioner
    """)

    # 9. Enable RLS on all application tables.
    tables = (
        "stores",
        "users",
        "members",
        "invites",
        "invoices",
        "products",
        "restock_batches",
        "restock_lines",
        "items",
        "payments",
        "stock_movements",
    )

    for table in tables:
        op.execute(
            f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY"
        )

    # 10. Remove existing policies so this migration can also
    # reproduce the configuration on the already-configured database.
    policies = {
        "stores": [
            "stores_insert_provisioner",
            "stores_select_members",
            "stores_update_managers",
        ],
        "users": [
            "users_insert_own",
            "users_insert_provisioner",
            "users_select_own",
            "users_update_own",
        ],
        "members": [
            "members_insert_provisioner",
            "members_select_active_members",
        ],
        "invites": [
            "invites_insert_managers",
            "invites_select_managers",
            "invites_update_managers",
        ],
        "invoices": [
            "invoices_insert_members",
            "invoices_select_members",
            "invoices_update_managers",
        ],
        "products": [
            "products_insert_managers",
            "products_select_members",
            "products_update_managers",
        ],
        "restock_batches": [
            "restock_batches_insert_managers",
            "restock_batches_select_members",
            "restock_batches_update_managers",
        ],
        "restock_lines": [
            "restock_lines_insert_managers",
            "restock_lines_select_members",
            "restock_lines_update_managers",
        ],
        "items": [
            "items_insert_members",
            "items_select_members",
        ],
        "payments": [
            "payments_insert_members",
            "payments_select_members",
        ],
        "stock_movements": [
            "stock_movements_insert_managers",
            "stock_movements_select_members",
        ],
    }

    for table, table_policies in policies.items():
        for policy in table_policies:
            op.execute(
                f"DROP POLICY IF EXISTS {policy} ON public.{table}"
            )

    # 11. Create RLS policies.

    policy_sql = [
        # Stores
        """
        CREATE POLICY stores_insert_provisioner
        ON public.stores FOR INSERT TO pasaley_provisioner
        WITH CHECK (true)
        """,
        """
        CREATE POLICY stores_select_members
        ON public.stores FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(id))
        """,
        """
        CREATE POLICY stores_update_managers
        ON public.stores FOR UPDATE TO pasaley_app
        USING (public.has_store_role(id, ARRAY['owner', 'manager']))
        WITH CHECK (public.has_store_role(id, ARRAY['owner', 'manager']))
        """,

        # Users
        """
        CREATE POLICY users_insert_own
        ON public.users FOR INSERT TO pasaley_app
        WITH CHECK (id = public.current_app_user_id())
        """,
        """
        CREATE POLICY users_insert_provisioner
        ON public.users FOR INSERT TO pasaley_provisioner
        WITH CHECK (true)
        """,
        """
        CREATE POLICY users_select_own
        ON public.users FOR SELECT TO pasaley_app
        USING (id = public.current_app_user_id())
        """,
        """
        CREATE POLICY users_update_own
        ON public.users FOR UPDATE TO pasaley_app
        USING (id = public.current_app_user_id())
        WITH CHECK (id = public.current_app_user_id())
        """,

        # Members
        """
        CREATE POLICY members_insert_provisioner
        ON public.members FOR INSERT TO pasaley_provisioner
        WITH CHECK (true)
        """,
        """
        CREATE POLICY members_select_active_members
        ON public.members FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,

        # Invites
        """
        CREATE POLICY invites_insert_managers
        ON public.invites FOR INSERT TO pasaley_app
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,
        """
        CREATE POLICY invites_select_managers
        ON public.invites FOR SELECT TO pasaley_app
        USING (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,
        """
        CREATE POLICY invites_update_managers
        ON public.invites FOR UPDATE TO pasaley_app
        USING (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,

        # Invoices
        """
        CREATE POLICY invoices_insert_members
        ON public.invoices FOR INSERT TO pasaley_app
        WITH CHECK (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY invoices_select_members
        ON public.invoices FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY invoices_update_managers
        ON public.invoices FOR UPDATE TO pasaley_app
        USING (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,

        # Products
        """
        CREATE POLICY products_insert_managers
        ON public.products FOR INSERT TO pasaley_app
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,
        """
        CREATE POLICY products_select_members
        ON public.products FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY products_update_managers
        ON public.products FOR UPDATE TO pasaley_app
        USING (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,

        # Restock batches
        """
        CREATE POLICY restock_batches_insert_managers
        ON public.restock_batches FOR INSERT TO pasaley_app
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,
        """
        CREATE POLICY restock_batches_select_members
        ON public.restock_batches FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY restock_batches_update_managers
        ON public.restock_batches FOR UPDATE TO pasaley_app
        USING (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,

        # Restock lines
        """
        CREATE POLICY restock_lines_insert_managers
        ON public.restock_lines FOR INSERT TO pasaley_app
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,
        """
        CREATE POLICY restock_lines_select_members
        ON public.restock_lines FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY restock_lines_update_managers
        ON public.restock_lines FOR UPDATE TO pasaley_app
        USING (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,

        # Items
        """
        CREATE POLICY items_insert_members
        ON public.items FOR INSERT TO pasaley_app
        WITH CHECK (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY items_select_members
        ON public.items FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,

        # Payments
        """
        CREATE POLICY payments_insert_members
        ON public.payments FOR INSERT TO pasaley_app
        WITH CHECK (public.is_active_store_member(store_id))
        """,
        """
        CREATE POLICY payments_select_members
        ON public.payments FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,

        # Stock movements
        """
        CREATE POLICY stock_movements_insert_managers
        ON public.stock_movements FOR INSERT TO pasaley_app
        WITH CHECK (
            public.has_store_role(store_id, ARRAY['owner', 'manager'])
        )
        """,
        """
        CREATE POLICY stock_movements_select_members
        ON public.stock_movements FOR SELECT TO pasaley_app
        USING (public.is_active_store_member(store_id))
        """,
    ]

    for statement in policy_sql:
        op.execute(statement)

    # 12. Automatic RLS for future public tables.
    op.execute("""
        CREATE OR REPLACE FUNCTION public.rls_auto_enable()
        RETURNS event_trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path TO 'pg_catalog'
        AS $function$
        DECLARE
            cmd record;
            tbl name;
        BEGIN
            FOR cmd IN
                SELECT *
                FROM pg_event_trigger_ddl_commands()
                WHERE command_tag IN (
                    'CREATE TABLE',
                    'CREATE TABLE AS',
                    'SELECT INTO'
                )
                  AND object_type IN ('table', 'partitioned table')
            LOOP
                IF cmd.schema_name IS NOT NULL
                   AND cmd.schema_name = 'public'
                   AND cmd.schema_name NOT IN (
                       'pg_catalog', 'information_schema'
                   )
                   AND cmd.schema_name NOT LIKE 'pg_toast%'
                   AND cmd.schema_name NOT LIKE 'pg_temp%'
                THEN
                    BEGIN
                        SELECT c.relname
                        INTO tbl
                        FROM pg_catalog.pg_class c
                        WHERE c.oid = cmd.objid;

                        EXECUTE format(
                            'ALTER TABLE IF EXISTS %I.%I ENABLE ROW LEVEL SECURITY',
                            cmd.schema_name,
                            tbl
                        );

                        RAISE LOG
                            'rls_auto_enable: enabled RLS on %',
                            cmd.object_identity;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE LOG
                                'rls_auto_enable: failed to enable RLS on %',
                                cmd.object_identity;
                    END;
                ELSE
                    RAISE LOG
                        'rls_auto_enable: skipped %',
                        cmd.object_identity;
                END IF;
            END LOOP;
        END;
        $function$;
    """)

    op.execute(
        "ALTER FUNCTION public.rls_auto_enable() OWNER TO postgres"
    )

    # Replace the existing trigger if this is the already-configured DB.
    op.execute("DROP EVENT TRIGGER IF EXISTS ensure_rls")

    op.execute("""
        CREATE EVENT TRIGGER ensure_rls
        ON ddl_command_end
        WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
        EXECUTE FUNCTION public.rls_auto_enable()
    """)


def downgrade() -> None:
    """Remove the Pasaley security layer."""

    op.execute("DROP EVENT TRIGGER IF EXISTS ensure_rls")

    policies = {
        "stores": [
            "stores_insert_provisioner",
            "stores_select_members",
            "stores_update_managers",
        ],
        "users": [
            "users_insert_own",
            "users_insert_provisioner",
            "users_select_own",
            "users_update_own",
        ],
        "members": [
            "members_insert_provisioner",
            "members_select_active_members",
        ],
        "invites": [
            "invites_insert_managers",
            "invites_select_managers",
            "invites_update_managers",
        ],
        "invoices": [
            "invoices_insert_members",
            "invoices_select_members",
            "invoices_update_managers",
        ],
        "products": [
            "products_insert_managers",
            "products_select_members",
            "products_update_managers",
        ],
        "restock_batches": [
            "restock_batches_insert_managers",
            "restock_batches_select_members",
            "restock_batches_update_managers",
        ],
        "restock_lines": [
            "restock_lines_insert_managers",
            "restock_lines_select_members",
            "restock_lines_update_managers",
        ],
        "items": [
            "items_insert_members",
            "items_select_members",
        ],
        "payments": [
            "payments_insert_members",
            "payments_select_members",
        ],
        "stock_movements": [
            "stock_movements_insert_managers",
            "stock_movements_select_members",
        ],
    }

    for table, table_policies in policies.items():
        for policy in table_policies:
            op.execute(
                f"DROP POLICY IF EXISTS {policy} ON public.{table}"
            )

    for table in (
        "stores",
        "users",
        "members",
        "invites",
        "invoices",
        "products",
        "restock_batches",
        "restock_lines",
        "items",
        "payments",
        "stock_movements",
    ):
        op.execute(
            f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY"
        )

    op.execute("""
        DROP FUNCTION IF EXISTS public.provision_initial_store(
            character varying,
            character varying,
            character varying,
            text
        )
    """)
    op.execute(
        "DROP FUNCTION IF EXISTS public.is_active_store_member(uuid)"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS public.has_store_role(uuid, text[])"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS public.current_app_user_id()"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS public.rls_auto_enable()"
    )

    # Remove the explicit table and schema grants introduced here.
    for table in (
        "users",
        "stores",
        "members",
        "invites",
        "invoices",
        "products",
        "restock_batches",
        "restock_lines",
        "items",
        "payments",
        "stock_movements",
    ):
        op.execute(
            f"REVOKE ALL PRIVILEGES ON TABLE public.{table} FROM pasaley_app"
        )

    for table in ("users", "stores", "members"):
        op.execute(
            f"REVOKE INSERT ON TABLE public.{table} FROM pasaley_provisioner"
        )

    op.execute("REVOKE USAGE ON SCHEMA public FROM pasaley_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM pasaley_provisioner")
