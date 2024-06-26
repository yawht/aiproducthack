"""
Data structures, used in project.

You may do changes in tables here, then execute
`alembic revision --message="Your text" --autogenerate`
"""

from datetime import datetime
from typing import List, Optional
import uuid
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
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

    uid: Mapped[uuid.UUID] = mapped_column(primary_key=True, type_=PGUUID, default=uuid.uuid4)
    status: Mapped[GenerationStatus]
    created_at: Mapped[datetime] = mapped_column(default=func.now(), type_=DateTime)
    meta: Mapped[dict] = mapped_column(nullable=False, server_default="{}", type_=JSONB)

    # NOTE img_path has schema {bucket}/{object_name}, ex: ya-art-gen-test/1f1fe1b3-a54de49d-b177a18e-846496de
    input_img_path: Mapped[str]
    description: Mapped[Optional[str]]
    input_prompt: Mapped[Optional[str]]
    negative_prompt: Mapped[Optional[str]]

    results: Mapped[List["GenerationResult"]] = relationship(
        back_populates="generation", cascade="all, delete-orphan"
    )

    @property
    def image_link(self) -> str:
        return f"http://158.160.151.53:9091/{self.input_img_path}"


class GenerationResult(Base):
    __tablename__ = "generation_result"

    uid: Mapped[uuid.UUID] = mapped_column(primary_key=True, type_=PGUUID, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(type_=DateTime)
    finished_at: Mapped[datetime] = mapped_column(default=func.now(), type_=DateTime)

    # NOTE img_path has schema {bucket}/{object_name}, ex: ya-art-source-test/1f1fe1b3-a54de49d-b177a18e-846496de
    img_path: Mapped[Optional[str]]
    error: Mapped[Optional[str]]

    generation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation.uid"), type_=PGUUID
    )

    generation: Mapped["Generation"] = relationship(back_populates="results")

    @property
    def image_link(self) -> str:
        return f"http://158.160.151.53:9091/{self.img_path}"
