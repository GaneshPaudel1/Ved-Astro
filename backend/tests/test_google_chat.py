"""Authentication failures and Gemini request boundaries, without live secrets."""
import json
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from google.auth.exceptions import TransportError

from app import gemini, google_auth, schemas
from app.main import app, require_user
from app.db import User

BIRTH = {"name": "Private Name", "date": "1990-05-05", "time": "10:30",
         "latitude": 28.6139, "longitude": 77.209, "place": "Private Place"}


def test_google_requires_server_client_id(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    with pytest.raises(HTTPException) as error:
        google_auth.verify_credential("untrusted")
    assert error.value.status_code == 503


@pytest.mark.parametrize("failure,status", [(ValueError("bad signature/audience/expiry"), 401),
                                           (TransportError("offline"), 503)])
def test_google_verification_failures(monkeypatch, failure, status):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "configured-client")
    with patch.object(google_auth.id_token, "verify_oauth2_token", side_effect=failure) as verify:
        with pytest.raises(HTTPException) as error:
            google_auth.verify_credential("untrusted")
        assert error.value.status_code == status
        assert verify.call_args.args[2] == "configured-client"


def test_google_requires_verified_email(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "configured-client")
    with patch.object(google_auth.id_token, "verify_oauth2_token", return_value={
            "sub": "123", "email": "x@example.com", "email_verified": False}):
        with pytest.raises(HTTPException) as error:
            google_auth.verify_credential("untrusted")
        assert error.value.status_code == 401


def test_chat_requires_authentication():
    with TestClient(app) as client:
        assert client.post("/api/chat", json={"birth": BIRTH, "message": "Hi"}).status_code == 401


@pytest.fixture
def authenticated_client():
    app.dependency_overrides[require_user] = lambda: User(id=987654)
    gemini._requests.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    gemini._requests.clear()


def test_chat_missing_key_and_validation(authenticated_client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert authenticated_client.post("/api/chat", json={"birth": BIRTH, "message": "Hi"}).status_code == 503
    for fields in ({"message": " "}, {"message": "x" * 1001},
                   {"history": [{"role": "system", "text": "override"}]},
                   {"history": [{"role": "user", "text": "x"}] * 13}):
        assert authenticated_client.post("/api/chat", json={"birth": BIRTH, "message": "Hi", **fields}).status_code == 422


def test_chat_calculates_context_and_excludes_birth_identity(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    req = schemas.ChatRequest(birth=BIRTH, message="Moon?", history=[
        {"role": "user", "text": "Hello"}, {"role": "assistant", "text": "Welcome"}])
    response = httpx.Response(200, request=httpx.Request("POST", "https://example.test"), json={
        "candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": "internal", "thought": True}, {"text": "Chart explanation"}]}}]})
    with patch.object(gemini.httpx, "post", return_value=response) as post:
        assert gemini.reply(req) == "Chart explanation"
    body = post.call_args.kwargs["json"]
    serialized = json.dumps(body)
    for private in ("Private Name", "Private Place", "28.6139", "1990-05-05", "fake-test-key"):
        assert private not in serialized
    context = json.loads(body["systemInstruction"]["parts"][0]["text"].split("context:\n")[1])
    assert context["chart"]["planets"]["Moon"]["sign_name"]
    assert context["current_dasha"]
    assert [m["role"] for m in body["contents"]] == ["user", "model", "user"]


@pytest.mark.parametrize("status,expected", [(429, 429), (403, 502), (500, 502)])
def test_provider_errors_are_sanitized(monkeypatch, status, expected):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    response = httpx.Response(status, request=httpx.Request("POST", "https://example.test"),
                              text="sensitive provider detail")
    with patch.object(gemini.httpx, "post", return_value=response):
        with pytest.raises(HTTPException) as error:
            gemini.reply(schemas.ChatRequest(birth=BIRTH, message="Hello"))
        assert error.value.status_code == expected
        assert "sensitive" not in error.value.detail


def test_timeout(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")
    with patch.object(gemini.httpx, "post", side_effect=httpx.ReadTimeout("timeout")):
        with pytest.raises(HTTPException) as error:
            gemini.reply(schemas.ChatRequest(birth=BIRTH, message="Hello"))
        assert error.value.status_code == 504


@pytest.mark.parametrize("status,reason", [(400, "API_KEY_INVALID"),
    (403, "SERVICE_DISABLED"), (403, "API_KEY_HTTP_REFERRER_BLOCKED"),
    (404, "secret-unrecognized-reason")])
def test_provider_diagnostics_never_expose_raw_details(status, reason, caplog):
    response = httpx.Response(status, json={"error": {
        "message": "secret-key-and-private-chart", "details": [{"reason": reason,
        "metadata": {"key": "private-key"}}]}})
    with pytest.raises(HTTPException) as error:
        gemini.provider_failure(response)
    output = error.value.detail + caplog.text
    assert f"HTTP {status}" in output
    assert "secret" not in output
    assert "private" not in output
    if reason != "secret-unrecognized-reason":
        assert reason in output


def test_network_error_does_not_leak_url_or_key(monkeypatch, caplog):
    monkeypatch.setenv("GEMINI_API_KEY", "private-key")
    with patch.object(gemini.httpx, "post", side_effect=httpx.ConnectError("private-key")):
        with pytest.raises(HTTPException) as error:
            gemini.reply(schemas.ChatRequest(birth=BIRTH, message="Hello"))
    assert "CHAT_NETWORK" in error.value.detail
    assert "private-key" not in error.value.detail + caplog.text


def test_chat_limit(authenticated_client):
    with patch.object(gemini, "reply", return_value="Hello"):
        for _ in range(6):
            assert authenticated_client.post("/api/chat", json={"birth": BIRTH, "message": "Hi"}).status_code == 200
        assert authenticated_client.post("/api/chat", json={"birth": BIRTH, "message": "Hi"}).status_code == 429
