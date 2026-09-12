"""Google Identity Services verification. Never trust browser-decoded claims."""
import os

from fastapi import HTTPException
from google.auth.exceptions import TransportError
from google.auth.transport.requests import Request
from google.oauth2 import id_token


def verify_credential(credential: str) -> dict:
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(503, "Google sign-in is not configured yet.")
    try:
        claims = id_token.verify_oauth2_token(credential, Request(), client_id)
    except TransportError:
        raise HTTPException(503, "Google sign-in is temporarily unavailable.") from None
    except ValueError:
        raise HTTPException(401, "Google sign-in could not be verified.") from None
    if not claims.get("sub") or not claims.get("email") or claims.get("email_verified") is not True:
        raise HTTPException(401, "A verified Google account is required.")
    return claims
