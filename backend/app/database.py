
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings #settings was created in config.py


class Base(DeclarativeBase):
    pass

# This is a base class for your SQLAlchemy database models.

# For example, imagine you have:
# class Product(Base):    __tablename__ = "products"

# By inheriting from Base, your Product class becomes part of SQLAlchemy's model metadata.
# Metadata is information about your database tables: their names, columns, constraints, relationships, and so on.

engine = create_engine( #An SQLAlchemy engine is the central object used to establish and manage database connections.
    settings.DATABASE_URL, #This means the application uses the pasaley_app connection string from .env.
    pool_pre_ping=True,
)


SessionLocal = sessionmaker( #A session is an object your backend uses to interact with the database during a unit of work.
    bind=engine,
    autoflush=False,
    autocommit=False, #autocommit=False means changes aren't automatically committed just because a query was executed. The application controls when to commit.
)
