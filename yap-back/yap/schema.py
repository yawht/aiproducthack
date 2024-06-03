"""
Data structures, used in project.

You may do changes in tables here, then execute
`alembic revision --message="Your text" --autogenerate`
"""

from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

import enum

from sqlalchemy import (
    DateTime,
    MetaData,
    func,
)


# see https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "all_column_names": lambda constraint, table: "_".join(
        [column.name for column in constraint.columns.values()]
    ),
    "ix": "ix__%(table_name)s__%(all_column_names)s",
    "uq": "uq__%(table_name)s__%(all_column_names)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": ("fk__%(table_name)s__%(all_column_names)s__" "%(referred_table_name)s"),
    "pk": "pk__%(table_name)s",
}

# Registry for all tables
metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    pass


class GenerationStatus(enum.Enum):
    created = "created"
    in_progress = "in_progress"
    finished = "finished"
    failed = "failed"


class Generation(Base):
    __tablename__ = "generation"

    uid: Mapped[uuid.UUID] = mapped_column(primary_key=True, type_=UUID)
    status: Mapped[GenerationStatus]

    created_at: Mapped[datetime] = mapped_column(default=func.now(), type_=DateTime)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), type_=DateTime
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(type_=DateTime)

    meta: Mapped[dict] = mapped_column(nullable=False, server_default="{}", type_=JSONB)
