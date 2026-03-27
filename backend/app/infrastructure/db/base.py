from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared SQLAlchemy declarative base.
    All module ORM models inherit from this.
    Each model specifies its own PostgreSQL schema via __table_args__.
    """
    pass
