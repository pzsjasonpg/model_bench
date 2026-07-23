"""Pydantic models + SQLAlchemy ORM models."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


# ── SQLAlchemy base ──────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── SQLAlchemy ORM models ────────────────────────────────────────────

class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    test_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    fixed_params = Column(Text, nullable=False)
    sweep_params = Column(Text, nullable=True)
    sweep_key = Column(String, nullable=True)
    sweep_values = Column(Text, nullable=True)
    num_subtasks = Column(Integer, nullable=False, default=0)
    completed_subtasks = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)
    started_at = Column(String, nullable=True)
    finished_at = Column(String, nullable=True)

    subtasks = relationship("SubTask", back_populates="test_run", lazy="selectin",
                            order_by="SubTask.seq")


class SubTask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    params = Column(Text, nullable=False)
    command = Column(Text, nullable=False)
    pid = Column(Integer, nullable=True)
    started_at = Column(String, nullable=True)
    finished_at = Column(String, nullable=True)
    result = Column(Text, nullable=True)

    test_run = relationship("TestRun", back_populates="subtasks")


class LogLine(Base):
    __tablename__ = "log_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    subtask_id = Column(Integer, ForeignKey("subtasks.id"), nullable=True)
    line = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)


# ── Pydantic models (API schemas) ────────────────────────────────────

class SubTaskOut(BaseModel):
    id: int
    test_run_id: int
    seq: int
    status: str
    params: str
    command: str
    pid: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    result: Optional[str] = None

    class Config:
        from_attributes = True


class TestRunOut(BaseModel):
    id: int
    name: str
    test_type: str
    status: str
    fixed_params: str
    sweep_params: Optional[str] = None
    sweep_key: Optional[str] = None
    sweep_values: Optional[str] = None
    num_subtasks: int
    completed_subtasks: int
    error_message: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    class Config:
        from_attributes = True


class TestRunDetailOut(TestRunOut):
    subtasks: List[SubTaskOut] = []


class CreateTestRequest(BaseModel):
    name: Optional[str] = None
    test_type: str
    fixed_params: Dict[str, Any] = Field(default_factory=dict)
    sweep_key: Optional[str] = None
    sweep_values: Optional[List[Any]] = None


class PaginatedResponse(BaseModel):
    items: List[TestRunOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Helpers ──────────────────────────────────────────────────────────

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an ORM object to a dict, expanding JSON string fields."""
    d = {}
    for c in obj.__table__.columns:
        val = getattr(obj, c.name)
        d[c.name] = val
    return d
