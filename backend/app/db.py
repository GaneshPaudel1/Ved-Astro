"""Database setup and models.

SQLite through SQLAlchemy. Birth profiles store *coordinates and the resolved
UTC offset*, not just a place name -- a chart must stay reproducible even if a
geocoder later returns something different for the same string.
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text, create_engine)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

DB_PATH = os.environ.get(
    "VEDIC_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "vedic.db"))
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False,
                       connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    display_name = Column(String(120), default="")
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=_now)

    profiles = relationship("BirthProfile", back_populates="owner",
                            cascade="all, delete-orphan")
    tokens = relationship("AuthToken", back_populates="user",
                          cascade="all, delete-orphan")


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=_now)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tokens")

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(32)


class BirthProfile(Base):
    __tablename__ = "birth_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=True, index=True)

    name = Column(String(160), nullable=False)
    relationship_label = Column(String(60), default="")   # self, mother, friend...

    birth_date = Column(String(10), nullable=False)       # YYYY-MM-DD
    birth_time = Column(String(8), nullable=True)         # HH:MM:SS, null = unknown

    place_name = Column(String(255), default="")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Resolved at save time and frozen, so the chart is reproducible.
    tz_name = Column(String(80), default="")
    utc_offset_hours = Column(Float, nullable=True)
    time_standard = Column(String(16), default="auto")

    ayanamsa = Column(String(24), default="lahiri")
    house_system = Column(String(24), default="whole_sign")
    node_type = Column(String(8), default="mean")

    notes = Column(Text, default="")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    owner = relationship("User", back_populates="profiles")

    @property
    def time_known(self) -> bool:
        return bool(self.birth_time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "relationship_label": self.relationship_label or "",
            "birth_date": self.birth_date,
            "birth_time": self.birth_time,
            "time_known": self.time_known,
            "place_name": self.place_name or "",
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tz_name": self.tz_name or "",
            "utc_offset_hours": self.utc_offset_hours,
            "time_standard": self.time_standard or "auto",
            "ayanamsa": self.ayanamsa,
            "house_system": self.house_system,
            "node_type": self.node_type,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def init_db() -> None:
    Base.metadata.create_all(ENGINE)


def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
