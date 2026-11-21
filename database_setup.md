# Pasaley — Database Setup Guide

This guide explains how each team member can configure their own Supabase development database.

## 1. Prerequisites

Install the following:

- Git
- Python 3.12
- PostgreSQL client (optional)
- A Supabase account
- VS Code or another code editor

## 2. Clone the Repository

Clone the Pasaley repository and switch to the development branch containing the database migrations.

```powershell
git clone <REPOSITORY_URL>
cd 5th-sem-project-pos-system
git checkout database
```

## 3. Create Your Own Supabase Project

1. Visit https://supabase.com.
2. Create a new Supabase project.
3. Give your project a name, such as `pasaley-dev-yourname`.
4. Create and securely save your database password.
5. Choose a region.
6. Wait until the database is ready.

**Important:** Every developer must use their own Supabase project. Do not connect to another developer's development database unless explicitly agreed.

## 4. Bootstrap PostgreSQL Roles

Open your Supabase project:

1. Navigate to SQL Editor.
2. Create a new query.
3. Open this file from the repository:

   `backend/database/bootstrap_roles.sql`

4. Copy its contents into the Supabase SQL Editor.
5. Execute the SQL.

This creates the required PostgreSQL roles:

- `pasaley_app` — application runtime role.
- `pasaley_provisioner` — restricted store-provisioning role.

## 5. Set the Application Role Password

The bootstrap script does not create a password for `pasaley_app`.

In Supabase SQL Editor, execute the following after replacing the placeholder with your own strong password:

```sql
ALTER ROLE pasaley_app
WITH PASSWORD 'YOUR_OWN_STRONG_PASSWORD';
```

Never commit this password to GitHub or share it in the team repository.

## 6. Configure the Python Environment

Open PowerShell inside the `backend` directory.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

## 7. Configure Environment Variables

Create a `.env` file inside `backend`.

Configure these two database connections:

```env
DATABASE_URL=postgresql://pasaley_app:APP_PASSWORD@YOUR_HOST:5432/postgres

MIGRATION_DATABASE_URL=postgresql://postgres:DB_PASSWORD@YOUR_HOST:5432/postgres
```

Replace the placeholders with your own Supabase connection information.

- `DATABASE_URL`: Uses the `pasaley_app` role for normal application database operations.
- `MIGRATION_DATABASE_URL`: Uses your project's database owner connection for Alembic migrations.

Use the connection details provided by your own Supabase project's Connect page. The connection URL format may differ depending on whether you use the direct connection or a pooler.

If a password contains special characters, URL-encode it before placing it in a connection URL.

**Security rules:**

- Never commit `.env`.
- Never share your database owner password.
- Never put database credentials in frontend code.
- Keep `MIGRATION_DATABASE_URL` private.

## 8. Run Database Migrations

Make sure your virtual environment is activated and your terminal is inside `backend`.

Run:

```powershell
alembic upgrade head
```

This applies the version-controlled migrations in order.

The migrations create:

- The initial Pasaley database schema.
- The database security functions.
- PostgreSQL permissions.
- Row Level Security policies.
- The automatic RLS event trigger.

Do not manually create the application tables. Alembic manages the database schema.

## 9. Verify the Database

Open Supabase SQL Editor and run:

```sql
SELECT version_num
FROM alembic_version;
```

The expected current migration revision is:

```text
6917bb725011
```

Verify Row Level Security:

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
      'stores', 'users', 'members', 'invites',
      'invoices', 'products', 'restock_batches',
      'restock_lines', 'items', 'payments',
      'stock_movements'
  )
ORDER BY tablename;
```

All 11 application tables should show `rowsecurity = true`.

## 10. Important Team Rules

1. Each developer uses their own Supabase development project.
2. Each developer manages their own `.env` file.
3. Never commit passwords, API keys, or database connection strings.
4. Use Alembic migrations for schema changes.
5. Commit new migration files to Git so the entire team can access them.
6. Do not run experimental migrations against another developer's database.
7. Coordinate before merging database changes into the shared `main` branch.

---

**Setup complete!**

You now have an independent Pasaley development database configured using the team's version-controlled migrations.