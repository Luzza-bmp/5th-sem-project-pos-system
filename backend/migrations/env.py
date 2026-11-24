
from logging.config import fileConfig

from sqlalchemy import pool

from alembic import context #	Gives access to Alembic's migration execution environment.

from app.config import settings
from app.database import Base
from sqlalchemy import create_engine
import app.models  # Import all models so Alembic can discover them


config = context.config #Access the Alembic configuration.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


#Base.metadata tells Alembic where our SQLAlchemy models are registered.
target_metadata = Base.metadata 


def run_migrations_offline() -> None: 
    """Run migrations without creating a database connection."""

    context.configure(
        url=settings.MIGRATION_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a privileged database connection."""

    migration_engine = create_engine(
        settings.MIGRATION_DATABASE_URL,
        poolclass=pool.NullPool, #pool.NullPool tells SQLAlchemy not to keep a reusable connection pool for this migration engine. It creates a connection for the operation and closes it afterward.
    )

    with migration_engine.connect() as connection: #This establishes a database connection and Uses the SQLAlchemy metadata we loaded.
        context.configure(      
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations() #runs the migration operations defined in your version files.

    migration_engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
