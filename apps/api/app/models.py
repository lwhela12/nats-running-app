from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    goals: Mapped[list[Goal]] = relationship(back_populates="user", cascade="all, delete-orphan")
    capabilities: Mapped[list[CapabilitySnapshot]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("age BETWEEN 13 AND 95", name="ck_users_age_range"),
        CheckConstraint("sex IN ('male','female','other')", name="ck_users_sex_values"),
    )


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    distance_m: Mapped[int] = mapped_column(Integer, nullable=False)
    target_time_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user: Mapped[User] = relationship(back_populates="goals")
    plans: Mapped[list[Plan]] = relationship(back_populates="goal", cascade="all, delete-orphan")


class CapabilitySnapshot(Base):
    __tablename__ = "capability_snapshots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    comfortable_distance_m: Mapped[int] = mapped_column(Integer, nullable=False)
    comfortable_time_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    projection: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user: Mapped[User] = relationship(back_populates="capabilities")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    user: Mapped[User] = relationship()
    goal: Mapped[Goal] = relationship(back_populates="plans")
    workouts: Mapped[list[Workout]] = relationship(back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('active','archived','superseded')", name="ck_plans_status_values"),
    )


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    plan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    wdate: Mapped[date] = mapped_column(Date, nullable=False)
    wtype: Mapped[str] = mapped_column(String, nullable=False)
    target_distance_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_zone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_key: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    plan: Mapped[Plan] = relationship(back_populates="workouts")

    __table_args__ = (
        CheckConstraint("wtype IN ('easy','long','tempo','interval','rest','cross')", name="ck_workouts_wtype_values"),
    )


class SessionLog(Base):
    __tablename__ = "session_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    workout_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    actual_distance_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_time_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rpe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)

    workout: Mapped[Workout] = relationship()

    __table_args__ = (
        CheckConstraint("rpe IS NULL OR (rpe BETWEEN 1 AND 10)", name="ck_session_logs_rpe_range"),
    )


class AdaptationEvent(Base):
    __tablename__ = "adaptation_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    plan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    rule: Mapped[str] = mapped_column(Text, nullable=False)
    before_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    after_state: Mapped[dict] = mapped_column(JSON, nullable=False)

    plan: Mapped[Plan] = relationship()


# Useful partial unique indexes can be created in migrations; app-level invariant:
# Only one active plan per goal.

