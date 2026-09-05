"""API surface: validation, auth boundaries, and end-to-end responses."""
from __future__ import annotations

import os
import tempfile

import pytest

# Point the app at a scratch database before it is imported.
os.environ["VEDIC_DB"] = os.path.join(tempfile.gettempdir(), "vedic_test.db")

from fastapi.testclient import TestClient          # noqa: E402
from app.main import app                            # noqa: E402
from app.db import Base, ENGINE                     # noqa: E402


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)
    with TestClient(app) as c:
        yield c


BIRTH = {"name": "Test", "date": "1990-05-05", "time": "10:30",
         "latitude": 28.6139, "longitude": 77.2090, "place": "New Delhi"}


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------
def test_health_reports_the_ephemeris_backend(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["engine"]["backend"] in ("Swiss", "Moshier", "JPL")
    assert "rule-based-v1" in body["interpreters"]


def test_reference_tables_are_complete(client):
    j = client.get("/api/reference").json()
    assert len(j["signs"]) == 12
    assert len(j["nakshatras"]) == 27
    assert len(j["planets"]) == 9
    assert len(j["houses"]) == 12
    assert len(j["vargas"]) == 16
    assert len(j["ayanamsas"]) == 4


# --------------------------------------------------------------------------
# Chart
# --------------------------------------------------------------------------
def test_chart_returns_every_section(client):
    b = client.post("/api/chart", json=BIRTH).json()
    for key in ("chart", "vargas", "dasha", "yogas", "ashtakavarga",
                "doshas", "transits", "interpretation", "nakshatra_detail"):
        assert key in b, key
    assert len(b["chart"]["planets"]) == 9
    assert len(b["chart"]["houses"]) == 12
    assert len(b["vargas"]) == 16
    assert b["ashtakavarga"]["sav_total"] == 337


def test_chart_include_filter_trims_the_payload(client):
    b = client.post("/api/chart", json={**BIRTH, "include": ["dasha"]}).json()
    assert "dasha" in b
    assert "vargas" not in b
    assert "ashtakavarga" not in b


def test_chart_without_time_flags_lagna_uncertain(client):
    b = client.post("/api/chart", json={**BIRTH, "time": None}).json()
    c = b["chart"]
    assert c["time_known"] is False
    assert c["ascendant"] is None
    assert c["houses"] == []
    assert any("time unknown" in w.lower() for w in c["warnings"])
    keys = [s["key"] for s in b["interpretation"]["sections"]]
    assert "lagna" in keys
    lagna = next(s for s in b["interpretation"]["sections"] if s["key"] == "lagna")
    assert "lagna-uncertain" in lagna["tags"]


def test_ayanamsa_switch_changes_the_result(client):
    a = client.post("/api/chart", json={**BIRTH, "ayanamsa": "lahiri",
                                        "include": ["chart"]}).json()
    b = client.post("/api/chart", json={**BIRTH, "ayanamsa": "raman",
                                        "include": ["chart"]}).json()
    assert a["chart"]["ayanamsa_value"] != b["chart"]["ayanamsa_value"]
    assert a["chart"]["planets"]["Sun"]["longitude"] != b["chart"]["planets"]["Sun"]["longitude"]


@pytest.mark.parametrize("payload,field", [
    ({"date": "1990-13-01"}, "date"),
    ({"date": "1990-02-30"}, "date"),
    ({"date": "not-a-date"}, "date"),
    ({"time": "25:00"}, "time"),
    ({"time": "10-30"}, "time"),
    ({"latitude": 91}, "latitude"),
    ({"longitude": -181}, "longitude"),
    ({"ayanamsa": "nonsense"}, "ayanamsa"),
    ({"house_system": "nonsense"}, "house_system"),
])
def test_invalid_input_is_rejected(client, payload, field):
    r = client.post("/api/chart", json={**BIRTH, **payload})
    assert r.status_code == 422, f"{field} should have been rejected"


def test_caching_returns_an_equivalent_chart(client):
    a = client.post("/api/chart", json=BIRTH).json()
    b = client.post("/api/chart", json=BIRTH).json()
    assert b["cached"] is True
    assert a["chart"]["planets"] == b["chart"]["planets"]
    # The live parts must still be recomputed, not frozen.
    assert b["dasha_path"]


# --------------------------------------------------------------------------
# Dasha, transits, panchang, match
# --------------------------------------------------------------------------
def test_dasha_endpoint_levels(client):
    r = client.post("/api/dasha", json={**BIRTH, "levels": 3}).json()
    assert r["total_years"] == 120
    assert len(r["periods"]) == 9
    assert len(r["periods"][0]["children"]) == 9
    assert len(r["periods"][0]["children"][0]["children"]) == 9
    assert len(r["current_path"]) == 5


@pytest.mark.parametrize("system,total", [("yogini", 36), ("ashtottari", 108)])
def test_alternate_dasha_systems(client, system, total):
    r = client.post("/api/dasha", json={**BIRTH, "system": system}).json()
    assert r["total_years"] == total


def test_transits_endpoint(client):
    r = client.post("/api/transits", json=BIRTH).json()
    assert len(r["transits"]["planets"]) == 9
    assert r["ingresses"]
    assert r["natal"]["ascendant_sign_name"]


def test_transits_accept_an_explicit_moment(client):
    r = client.post("/api/transits", json={**BIRTH, "at": "2030-01-01T00:00:00Z"})
    assert r.status_code == 200
    assert r.json()["transits"]["moment"].startswith("2030-01-01")


def test_transits_reject_a_bad_moment(client):
    r = client.post("/api/transits", json={**BIRTH, "at": "not-a-time"})
    assert r.status_code == 400


def test_panchang_endpoint(client):
    r = client.post("/api/panchang", json={
        "date": "2026-08-23", "latitude": 28.6139, "longitude": 77.2090}).json()
    assert r["vara"]["name"] == "Sunday"
    for limb in ("tithi", "nakshatra", "yoga", "karana"):
        assert r[limb]["name"]
    assert r["periods"]["rahu_kaal"]["start"]


def test_panchang_range(client):
    r = client.get("/api/panchang/range", params={
        "start": "2026-08-23", "days": 5,
        "latitude": 28.6139, "longitude": 77.2090}).json()
    assert len(r["entries"]) == 5


def test_match_endpoint(client):
    r = client.post("/api/match", json={
        "first": {**BIRTH, "name": "A"},
        "second": {"name": "B", "date": "1992-11-17", "time": "04:15",
                   "latitude": 19.0760, "longitude": 72.8777}}).json()
    assert r["maximum"] == 36.0
    assert len(r["kootas"]) == 8
    assert r["manglik"]["verdict"] in ("balanced", "clear", "mismatched")
    assert r["caveat"]


def test_geocode_builtin_works_offline(client):
    r = client.get("/api/geocode", params={"q": "Porbandar"}).json()
    assert r["results"]
    assert any("Porbandar" in x["name"] for x in r["results"])


def test_timezone_endpoint_detects_pre_standard_time(client):
    r = client.get("/api/timezone", params={
        "latitude": 21.6417, "longitude": 69.6293, "date": "1869-10-02"}).json()
    assert r["pre_standard_time"] is True
    assert r["note"]
    r2 = client.get("/api/timezone", params={
        "latitude": 28.6139, "longitude": 77.2090, "date": "2000-01-01"}).json()
    assert r2["pre_standard_time"] is False
    assert r2["utc_offset_hours"] == 5.5


# --------------------------------------------------------------------------
# Auth and profiles
# --------------------------------------------------------------------------
def test_profiles_require_authentication(client):
    assert client.get("/api/profiles").status_code == 401
    assert client.post("/api/profiles", json=BIRTH).status_code == 401


def test_register_login_and_profile_lifecycle(client):
    reg = client.post("/api/auth/register", json={
        "email": "Reader@Example.com", "password": "a-long-password",
        "display_name": "Reader"})
    assert reg.status_code == 200
    token = reg.json()["token"]
    auth = {"Authorization": f"Bearer {token}"}
    assert reg.json()["user"]["email"] == "reader@example.com"

    # Duplicate registration is refused.
    assert client.post("/api/auth/register", json={
        "email": "reader@example.com", "password": "a-long-password"}
    ).status_code == 409

    me = client.get("/api/auth/me", headers=auth).json()
    assert me["email"] == "reader@example.com"

    created = client.post("/api/profiles", headers=auth, json={
        **BIRTH, "name": "Self", "relationship_label": "self"})
    assert created.status_code == 201
    pid = created.json()["id"]
    # The offset is resolved and frozen at save time.
    assert created.json()["utc_offset_hours"] == 5.5
    assert created.json()["tz_name"] == "Asia/Kolkata"

    assert len(client.get("/api/profiles", headers=auth).json()["profiles"]) == 1

    patched = client.patch(f"/api/profiles/{pid}", headers=auth,
                           json={"notes": "checked against the certificate"})
    assert patched.json()["notes"] == "checked against the certificate"

    ch = client.get(f"/api/profiles/{pid}/chart", headers=auth).json()
    assert ch["chart"]["ascendant_sign_name"]
    assert ch["name"] == "Self"

    assert client.delete(f"/api/profiles/{pid}", headers=auth).status_code == 204
    assert client.get(f"/api/profiles/{pid}", headers=auth).status_code == 404


def test_users_cannot_read_each_others_profiles(client):
    a = client.post("/api/auth/register", json={
        "email": "one@example.com", "password": "a-long-password"}).json()
    b = client.post("/api/auth/register", json={
        "email": "two@example.com", "password": "a-long-password"}).json()
    a_auth = {"Authorization": f"Bearer {a['token']}"}
    b_auth = {"Authorization": f"Bearer {b['token']}"}

    pid = client.post("/api/profiles", headers=a_auth,
                      json={**BIRTH, "name": "Private"}).json()["id"]

    assert client.get(f"/api/profiles/{pid}", headers=b_auth).status_code == 404
    assert client.delete(f"/api/profiles/{pid}", headers=b_auth).status_code == 404
    assert client.get(f"/api/profiles/{pid}/chart", headers=b_auth).status_code == 404
    assert client.get(f"/api/profiles/{pid}", headers=a_auth).status_code == 200


def test_login_rejects_a_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "three@example.com", "password": "a-long-password"})
    assert client.post("/api/auth/login", json={
        "email": "three@example.com", "password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json={
        "email": "three@example.com", "password": "a-long-password"}).status_code == 200


def test_short_password_is_refused(client):
    assert client.post("/api/auth/register", json={
        "email": "four@example.com", "password": "short"}).status_code == 422
