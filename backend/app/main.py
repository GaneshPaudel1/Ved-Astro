"""FastAPI application.

Routes are thin: validate, call a service, return. Every astrological decision
lives in app.jyotish, every sentence in app.interpret.
"""
from __future__ import annotations

import os
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import geocode, schemas, services, google_auth, gemini
from .db import AccountLibrary, AuthToken, BirthProfile, GoogleIdentity, User, get_session, init_db
from sqlalchemy.exc import IntegrityError
from .interpret.engine import available as interpreters_available
from .jyotish import constants as K
from .jyotish import dasha as dasha_mod
from .jyotish import panchang as panchang_mod
from .jyotish import transits as transits_mod
from .jyotish import vargas as vargas_mod
from .jyotish.ephemeris import ephemeris_backend
from .jyotish.timeutil import julian_day, timezone_for, utc_offset_at

app = FastAPI(
    title="Jyotish API",
    description="Sidereal Vedic astrology calculations backed by the Swiss Ephemeris.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[s.strip() for s in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if s.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


# --------------------------------------------------------------------------
# Auth helpers
# --------------------------------------------------------------------------
def current_user(authorization: str | None = Header(default=None),
                 db: Session = Depends(get_session)) -> User | None:
    """Optional auth. Anonymous use is fully supported; accounts only add
    saved profiles."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    row = db.query(AuthToken).filter(AuthToken.token == token).first()
    if not row:
        return None
    if row.expires_at and row.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return None
    return row.user


def require_user(user: User | None = Depends(current_user)) -> User:
    if user is None:
        raise HTTPException(401, "Sign in with Google to continue.")
    return user


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------
@app.get("/")
def root() -> dict[str, Any]:
    """Hitting the API host directly should explain itself, not 404."""
    return {
        "service": "Jyotish API",
        "docs": "/docs",
        "health": "/api/health",
        "note": ("This is the calculation backend. The web interface runs "
                 "separately (npm run dev in ./frontend, port 5173)."),
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "engine": ephemeris_backend(),
        "cache": services.cache_stats(),
        "interpreters": interpreters_available(),
    }


@app.get("/api/reference")
def reference() -> dict[str, Any]:
    """Static tables the frontend renders: signs, nakshatras, options."""
    return {
        "signs": [
            {"index": i, "name": n, "sanskrit": s, "lord": l,
             "element": e, "quality": q, "symbol": sym}
            for i, (n, s, l, e, q, sym) in enumerate(K.SIGNS)
        ],
        "nakshatras": [
            {"index": i, "number": i + 1, "name": n[0], "lord": n[1],
             "deity": n[2], "symbol": n[3], "gana": n[4], "nadi": n[5],
             "yoni": n[6], "yoni_sex": n[7],
             "start": round(i * K.NAKSHATRA_SPAN, 4),
             "end": round((i + 1) * K.NAKSHATRA_SPAN, 4)}
            for i, n in enumerate(K.NAKSHATRAS)
        ],
        "planets": [
            {"name": p, "sanskrit": K.PLANET_SANSKRIT[p],
             "glyph": K.PLANET_GLYPH[p], "abbr": K.PLANET_ABBR[p],
             "benefic": p in K.NATURAL_BENEFICS}
            for p in K.PLANETS
        ],
        "houses": [
            {"number": i + 1, "meaning": m}
            for i, m in enumerate(K.HOUSE_MEANINGS)
        ],
        "ayanamsas": schemas.ayanamsa_catalogue(),
        "house_systems": [
            {"key": "whole_sign", "label": "Whole sign (Rashi)",
             "note": "The classical Vedic default. Each sign is one house."},
            {"key": "placidus", "label": "Placidus",
             "note": "Time-based cusps. Used in KP; undefined near the poles."},
            {"key": "sripati", "label": "Sripati / Porphyry",
             "note": "Space-based cusps, used in some North Indian schools."},
            {"key": "equal", "label": "Equal house", "note": "30 degrees from the lagna."},
            {"key": "koch", "label": "Koch", "note": "Undefined near the poles."},
        ],
        "vargas": [
            {"key": v, "name": vargas_mod.VARGAS[v]["name"],
             "divisions": vargas_mod.VARGAS[v]["divisions"],
             "signifies": vargas_mod.VARGAS[v]["signifies"]}
            for v in vargas_mod.VARGA_ORDER
        ],
    }


# --------------------------------------------------------------------------
# Geocoding
# --------------------------------------------------------------------------
@app.get("/api/geocode")
async def geocode_search(q: str = Query(min_length=1, max_length=120),
                         limit: int = Query(default=8, ge=1, le=20)):
    return await geocode.search(q, limit)


@app.get("/api/timezone")
def timezone_lookup(latitude: float = Query(ge=-90, le=90),
                    longitude: float = Query(ge=-180, le=180),
                    date: str | None = None) -> dict[str, Any]:
    """The historical offset for a place on a date -- shown in the birth form
    so the user can see which offset the chart will actually use."""
    tz = timezone_for(latitude, longitude)
    when = datetime.now()
    if date:
        y, m, d = (int(p) for p in date.split("-"))
        when = datetime(y, m, d, 12, 0)
    offset, tz, abbrev = utc_offset_at(latitude, longitude, when, tz)
    from .jyotish.timeutil import is_pre_standard_time, lmt_offset
    pre_standard = is_pre_standard_time(abbrev, offset)
    return {
        "tz_name": tz,
        "utc_offset_hours": offset,
        "abbreviation": abbrev,
        "pre_standard_time": pre_standard,
        "lmt_offset_hours": lmt_offset(longitude),
        "note": ("This date predates standard time here, so the chart will use "
                 "Local Mean Time for the birth longitude."
                 if pre_standard else None),
    }


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
@app.post("/api/chart")
def chart(req: schemas.ChartRequest, user: User = Depends(require_user)) -> dict[str, Any]:
    return services.build_bundle(
        name=req.name, date=req.date, time=req.time,
        latitude=req.latitude, longitude=req.longitude, place=req.place,
        ayanamsa=req.ayanamsa, house_system=req.house_system,
        node_type=req.node_type, time_standard=req.time_standard,
        tz_name=req.tz_name, utc_offset_override=req.utc_offset_override,
        include=set(req.include) if req.include else None)


@app.post("/api/dasha")
def dasha_detail(req: schemas.DashaExpandRequest) -> dict[str, Any]:
    """Deeper dasha levels on demand -- expanding all five for all nine lords
    would be 59,049 nodes, so the tree is served shallow and drilled into."""
    bundle = services.build_bundle(
        name=req.name, date=req.date, time=req.time,
        latitude=req.latitude, longitude=req.longitude, place=req.place,
        ayanamsa=req.ayanamsa, time_standard=req.time_standard,
        tz_name=req.tz_name, utc_offset_override=req.utc_offset_override,
        include={"dasha"})
    moon = bundle["chart"]["planets"]["Moon"]["longitude"]
    jd = bundle["chart"]["moment"]["jd_ut"]
    now = services.now_jd()

    if req.system == "yogini":
        tree = dasha_mod.yogini(moon, jd, now_jd=now)
    elif req.system == "ashtottari":
        tree = dasha_mod.ashtottari(moon, jd, now_jd=now)
    else:
        tree = dasha_mod.vimshottari(moon, jd, now_jd=now, max_level=req.levels)
        tree["current_path"] = dasha_mod.current_dasha_path(tree, now, depth=5)
    return tree


@app.post("/api/transits")
def transit_view(req: schemas.TransitRequest) -> dict[str, Any]:
    bundle = services.build_bundle(
        name=req.name, date=req.date, time=req.time,
        latitude=req.latitude, longitude=req.longitude, place=req.place,
        ayanamsa=req.ayanamsa, time_standard=req.time_standard,
        tz_name=req.tz_name, utc_offset_override=req.utc_offset_override,
        include={"ashtakavarga"})

    if req.at:
        try:
            when = datetime.fromisoformat(req.at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(400, f"could not read 'at': {exc}") from exc
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        jd = julian_day(when.astimezone(timezone.utc))
    else:
        jd = services.now_jd()

    chart_d = bundle["chart"]
    bav = (bundle.get("ashtakavarga") or {}).get("bav")
    return {
        "transits": transits_mod.compute(chart_d["planets"],
                                         chart_d["ascendant_sign"], jd,
                                         ayanamsa=req.ayanamsa, bav=bav),
        "alerts": transits_mod.alerts(chart_d["planets"], jd, ayanamsa=req.ayanamsa),
        "ingresses": transits_mod.next_ingresses(jd, ayanamsa=req.ayanamsa),
        "natal": {
            "ascendant_sign": chart_d["ascendant_sign"],
            "ascendant_sign_name": chart_d.get("ascendant_sign_name"),
            "planets": {n: {"sign": p["sign"], "sign_name": p["sign_name"],
                            "longitude": p["longitude"], "abbr": p["abbr"],
                            "degree_str": p["degree_str"]}
                        for n, p in chart_d["planets"].items()},
            "time_known": chart_d["time_known"],
        },
    }


@app.post("/api/panchang")
def panchang_view(req: schemas.PanchangRequest) -> dict[str, Any]:
    return panchang_mod.compute(req.date, req.latitude, req.longitude,
                                ayanamsa=req.ayanamsa, tz_name=req.tz_name)


@app.get("/api/panchang/range")
def panchang_range(start: str, days: int = Query(default=7, ge=1, le=31),
                   latitude: float = Query(ge=-90, le=90),
                   longitude: float = Query(ge=-180, le=180),
                   ayanamsa: str = "lahiri") -> dict[str, Any]:
    y, m, d = (int(p) for p in start.split("-"))
    base = datetime(y, m, d)
    out = []
    for i in range(days):
        day = base + timedelta(days=i)
        out.append(panchang_mod.compute(day.strftime("%Y-%m-%d"),
                                        latitude, longitude, ayanamsa=ayanamsa))
    return {"start": start, "days": days, "entries": out}


@app.post("/api/match")
def match(req: schemas.MatchRequest) -> dict[str, Any]:
    return services.build_match(req.first.model_dump(), req.second.model_dump(),
                                ayanamsa=req.ayanamsa)


# --------------------------------------------------------------------------
# Accounts
# --------------------------------------------------------------------------
@app.get("/api/auth/config")
def auth_config():
    return {"google_client_id": os.environ.get("GOOGLE_CLIENT_ID", "").strip(),
            "chat_enabled": bool(os.environ.get("GEMINI_API_KEY", "").strip())}


@app.post("/api/auth/google")
def google_login(req: schemas.GoogleLoginRequest,
                 db: Session = Depends(get_session)) -> dict[str, Any]:
    claims = google_auth.verify_credential(req.credential)
    identity = db.get(GoogleIdentity, claims["sub"])
    if identity:
        return _issue_token(db, identity.user)
    email = claims["email"].strip().lower()
    # Never silently merge a legacy account based only on an email address.
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "This email has an existing account. Contact the site owner to migrate it to Google sign-in.")
    user = User(email=email, display_name=str(claims.get("name", ""))[:120],
                password_salt=secrets.token_hex(16), password_hash="google-only")
    db.add(user)
    try:
        db.flush()
        db.add(GoogleIdentity(subject=claims["sub"], user_id=user.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account creation changed. Please try signing in again.") from None
    return _issue_token(db, user)


@app.post("/api/chat")
def chart_chat(req: schemas.ChatRequest, user: User = Depends(require_user)):
    gemini.check_rate_limit(user.id)
    return {"reply": gemini.reply(req)}


def _issue_token(db: Session, user: User) -> dict[str, Any]:
    token = AuthToken(token=AuthToken.new_token(), user_id=user.id,
                      expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
                      + timedelta(days=30))
    db.add(token)
    db.commit()
    return {"token": token.token,
            "user": {"id": user.id, "email": user.email,
                     "display_name": user.display_name},
            "expires_at": token.expires_at.isoformat()}


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None),
           db: Session = Depends(get_session)) -> dict[str, str]:
    if authorization and authorization.lower().startswith("bearer "):
        tok = authorization.split(" ", 1)[1].strip()
        row = db.query(AuthToken).filter(AuthToken.token == tok).first()
        if row:
            db.delete(row)
            db.commit()
    return {"status": "signed out"}


@app.get("/api/auth/me")
def me(user: User = Depends(require_user)) -> dict[str, Any]:
    return {"id": user.id, "email": user.email,
            "display_name": user.display_name,
            "profile_count": len(user.profiles)}


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------
@app.get("/api/library")
def read_library(user: User = Depends(require_user), db: Session = Depends(get_session)):
    row = db.get(AccountLibrary, user.id)
    return {"revision": row.revision if row else 0,
            "charts": json.loads(row.charts_json) if row else []}


@app.put("/api/library")
def update_library(req: schemas.LibraryUpdate, user: User = Depends(require_user),
                   db: Session = Depends(get_session)):
    payload = json.dumps([c.model_dump() for c in req.charts])
    # Atomic compare-and-swap prevents lost edits and resurrected deletions.
    if req.revision == 0:
        db.add(AccountLibrary(user_id=user.id, revision=1, charts_json=payload))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Your collection changed on another device. Refresh and try again.") from None
    else:
        changed = db.query(AccountLibrary).filter(
            AccountLibrary.user_id == user.id,
            AccountLibrary.revision == req.revision).update(
                {"revision": req.revision + 1, "charts_json": payload})
        if not changed:
            db.rollback()
            raise HTTPException(409, "Your collection changed on another device. Refresh and try again.")
        db.commit()
    return {"revision": req.revision + 1}


@app.get("/api/profiles")
def list_profiles(user: User = Depends(require_user),
                  db: Session = Depends(get_session)) -> dict[str, Any]:
    rows = (db.query(BirthProfile)
            .filter(BirthProfile.user_id == user.id)
            .order_by(BirthProfile.updated_at.desc()).all())
    return {"profiles": [r.to_dict() for r in rows]}


@app.post("/api/profiles", status_code=201)
def create_profile(req: schemas.ProfileCreate,
                   user: User = Depends(require_user),
                   db: Session = Depends(get_session)) -> dict[str, Any]:
    # Resolve and freeze the offset now, so the chart stays reproducible.
    when = datetime.fromisoformat(f"{req.date}T{req.time or '12:00:00'}")
    offset, tz_name, _ = utc_offset_at(req.latitude, req.longitude, when, req.tz_name)

    row = BirthProfile(
        user_id=user.id, name=req.name.strip(),
        relationship_label=req.relationship_label,
        birth_date=req.date, birth_time=req.time,
        place_name=req.place, latitude=req.latitude, longitude=req.longitude,
        tz_name=tz_name, utc_offset_hours=req.utc_offset_override or offset,
        time_standard=req.time_standard, ayanamsa=req.ayanamsa,
        house_system=req.house_system, node_type=req.node_type,
        notes=req.notes)
    db.add(row)
    db.commit()
    return row.to_dict()


@app.get("/api/profiles/{profile_id}")
def read_profile(profile_id: int, user: User = Depends(require_user),
                 db: Session = Depends(get_session)) -> dict[str, Any]:
    return _owned(db, user, profile_id).to_dict()


@app.patch("/api/profiles/{profile_id}")
def update_profile(profile_id: int, req: schemas.ProfileUpdate,
                   user: User = Depends(require_user),
                   db: Session = Depends(get_session)) -> dict[str, Any]:
    row = _owned(db, user, profile_id)
    mapping = {"date": "birth_date", "time": "birth_time", "place": "place_name",
               "utc_offset_override": "utc_offset_hours"}
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(row, mapping.get(field, field), value)
    db.commit()
    return row.to_dict()


@app.delete("/api/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int, user: User = Depends(require_user),
                   db: Session = Depends(get_session)):
    row = _owned(db, user, profile_id)
    db.delete(row)
    db.commit()
    return JSONResponse(status_code=204, content=None)


@app.get("/api/profiles/{profile_id}/chart")
def profile_chart(profile_id: int, user: User = Depends(require_user),
                  db: Session = Depends(get_session)) -> dict[str, Any]:
    row = _owned(db, user, profile_id)
    return services.build_bundle(
        name=row.name, date=row.birth_date, time=row.birth_time,
        latitude=row.latitude, longitude=row.longitude, place=row.place_name,
        ayanamsa=row.ayanamsa, house_system=row.house_system,
        node_type=row.node_type, time_standard=row.time_standard or "auto",
        tz_name=row.tz_name or None)


def _owned(db: Session, user: User, profile_id: int) -> BirthProfile:
    row = db.get(BirthProfile, profile_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Profile not found.")
    return row
