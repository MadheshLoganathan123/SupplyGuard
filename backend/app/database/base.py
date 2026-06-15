"""
Declarative base — import all models here so Alembic can detect them.
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return cls.__name__.lower()


# Import models so Base.metadata knows about them
from app.models import *  # noqa: F401, E402
