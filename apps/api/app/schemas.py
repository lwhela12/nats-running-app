from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Auth
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    age: int = Field(ge=13, le=95)
    sex: str = Field(pattern=r"^(male|female|other)$")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Capability
class CapabilityCreate(BaseModel):
    date: date
    comfortable_distance_m: int = Field(ge=500, le=100000)
    comfortable_time_sec: int = Field(ge=120, le=20000)


class CapabilityOut(BaseModel):
    id: str
    date: date
    comfortable_distance_m: int
    comfortable_time_sec: int
    projection: dict


# Goals
class GoalCreate(BaseModel):
    distance_m: int = Field(ge=1000, le=100000)
    target_time_sec: Optional[int] = Field(default=None, ge=300, le=200000)
    target_date: date


class GoalOut(BaseModel):
    id: str
    distance_m: int
    target_time_sec: Optional[int]
    target_date: date


class FeasibilityResult(BaseModel):
    feasible: bool
    reasons: list[str]
    tradeoffs: list[dict]


# Plans & Workouts
class WorkoutOut(BaseModel):
    id: str
    wdate: date
    wtype: str
    target_distance_m: Optional[int]
    target_duration_sec: Optional[int]
    target_zone: Optional[str]
    description: Optional[str]
    is_key: bool


class PlanOut(BaseModel):
    id: str
    start_date: date
    end_date: date
    status: str
    workouts: list[WorkoutOut]


class LogCreate(BaseModel):
    actual_distance_m: Optional[int] = Field(default=None, ge=0)
    actual_time_sec: Optional[int] = Field(default=None, ge=0)
    rpe: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = None

