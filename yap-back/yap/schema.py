"""
Data structures, used in project.

You may do changes in tables here, then execute
`alembic revision --message="Your text" --autogenerate`
"""

from sqlalchemy.dialects.postgresql import UUID, JSONB

import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    MetaData,
    Table,
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


class Status(enum.Enum):
    created = "created"
    in_progress = "in_progress"
    finished = "finished"
    failed = "failed"


generation_table = Table(
    "generation",
    metadata,
    Column("uid", UUID, primary_key=True),
    Column(
        "status", Enum(Status, name="status"), nullable=False, default=Status.created
    ),
    Column("created_at", DateTime, nullable=False, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    Column("finished_at", DateTime, default=func.now()),
    # For non-normalized data, defined in app, for example input links
    Column("metadata", JSONB, nullable=False, server_default="{}"),
)
