"""Request and response shapes.

Validation lives here rather than in the routes so that a bad date or an
impossible latitude is rejected before it ever reaches the ephemeris.
"""
from __future__ import annotations

import re
from datetime import date as _date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .jyotish.constants import AYANAMSA_OPTIONS

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")

AyanamsaName = Literal["lahiri", "raman", "kp", "yukteshwar"]
HouseSystem = Literal["whole_sign", "placidus", "koch", "equal", "sripati"]
NodeType = Literal["mean", "true"]
TimeStandard = Literal["auto", "zone", "lmt"]


class BirthInput(BaseModel):
    gender: Literal["female", "male", "other", "prefer_not_to_say"] | None = None
    name: str = Field(default="", max_length=160)
    date: str
    time: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    place: str = Field(default="", max_length=255)
    tz_name: str | None = None
    utc_offset_override: float | None = Field(default=None, ge=-14, le=14)
    time_standard: TimeStandard = "auto"
    ayanamsa: AyanamsaName = "lahiri"
    house_system: HouseSystem = "whole_sign"
    node_type: NodeType = "mean"

    @field_validator("date")
    @classmethod
    def _check_date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError("date must be YYYY-MM-DD")
        y, m, d = (int(p) for p in v.split("-"))
        try:
            _date(y, m, d)
        except ValueError as exc:
            raise ValueError(f"not a real calendar date: {exc}") from exc
        # Swiss Ephemeris covers a very wide range, but a birth date outside
        # this window is far more likely to be a typo than a real entry.
        if not (1000 <= y <= 2200):
            raise ValueError("date must fall between year 1000 and 2200")
        return v

    @field_validator("time")
    @classmethod
    def _check_time(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        if not TIME_RE.match(v):
            raise ValueError("time must be HH:MM or HH:MM:SS")
        parts = [int(p) for p in v.split(":")]
        hh, mm = parts[0], parts[1]
        ss = parts[2] if len(parts) > 2 else 0
        if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
            raise ValueError("time is out of range")
        return f"{hh:02d}:{mm:02d}:{ss:02d}"


class ChartRequest(BirthInput):
    include: list[str] | None = None


class LibraryChart(BaseModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    birth: BirthInput
    savedAt: str = Field(min_length=1, max_length=40)


class LibraryUpdate(BaseModel):
    revision: int = Field(ge=0)
    charts: list[LibraryChart] = Field(max_length=100)

    @model_validator(mode="after")
    def unique_ids(self):
        if len({chart.id for chart in self.charts}) != len(self.charts):
            raise ValueError("Chart IDs must be unique")
        return self


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1, max_length=10000)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    birth: BirthInput
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @field_validator("message")
    @classmethod
    def nonempty_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message cannot be blank")
        return value.strip()


class ProfileCreate(BirthInput):
    relationship_label: str = Field(default="", max_length=60)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def _require_name(self):
        if not self.name.strip():
            raise ValueError("name is required for a saved profile")
        return self


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    relationship_label: str | None = Field(default=None, max_length=60)
    date: str | None = None
    time: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    place: str | None = Field(default=None, max_length=255)
    tz_name: str | None = None
    utc_offset_override: float | None = Field(default=None, ge=-14, le=14)
    time_standard: TimeStandard | None = None
    ayanamsa: AyanamsaName | None = None
    house_system: HouseSystem | None = None
    node_type: NodeType | None = None
    notes: str | None = Field(default=None, max_length=4000)

    _check_date = field_validator("date")(ChartRequest._check_date.__func__)
    _check_time = field_validator("time")(ChartRequest._check_time.__func__)


class PanchangRequest(BaseModel):
    date: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    ayanamsa: AyanamsaName = "lahiri"
    tz_name: str | None = None

    _check_date = field_validator("date")(ChartRequest._check_date.__func__)


class MatchRequest(BaseModel):
    first: BirthInput
    second: BirthInput
    ayanamsa: AyanamsaName = "lahiri"


class DashaExpandRequest(BirthInput):
    system: Literal["vimshottari", "yogini", "ashtottari"] = "vimshottari"
    levels: int = Field(default=2, ge=1, le=5)


class TransitRequest(BirthInput):
    at: str | None = None       # ISO datetime; defaults to now


class RegisterRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(default="", max_length=120)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or v.startswith("@") or v.endswith("@") or " " in v:
            raise ValueError("enter a valid email address")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


def ayanamsa_catalogue() -> list[dict[str, Any]]:
    return [{"key": k, **{kk: vv for kk, vv in v.items() if kk != "swe_id"}}
            for k, v in AYANAMSA_OPTIONS.items()]
