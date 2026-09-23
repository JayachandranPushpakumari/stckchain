import hashlib
import hmac
import os
import secrets
import time

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

APP_USERNAME = os.getenv("APP_USERNAME", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
DEMO_AUTH_ENABLED = os.getenv("ENABLE_DEMO_AUTH", "false").lower() == "true"
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "")
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", str(7 * 24 * 60 * 60)))

router = APIRouter()


def _secret() -> bytes:
    configured = os.getenv("TOKEN_SECRET", "")
    material = configured or f"{APP_USERNAME}:{APP_PASSWORD}"
    return hashlib.sha256(material.encode()).digest()


def _issue_token(username: str) -> str:
    expiry = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{username}.{expiry}"
    signature = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def _is_valid_token(token: str) -> bool:
    try:
        username, expiry, signature = token.rsplit(".", 2)
    except ValueError:
        return False
    payload = f"{username}.{expiry}"
    expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(signature, expected):
        return False
    return int(expiry) > time.time()


def require_auth(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    if not _is_valid_token(authorization.removeprefix("Bearer ").strip()):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
def login(body: LoginRequest):
    if not APP_USERNAME or not APP_PASSWORD:
        raise HTTPException(status_code=503, detail="Auth not configured on server")

    valid = (
        secrets.compare_digest(body.username, APP_USERNAME)
        and secrets.compare_digest(body.password, APP_PASSWORD)
    ) or (
        DEMO_AUTH_ENABLED
        and bool(DEMO_USERNAME)
        and bool(DEMO_PASSWORD)
        and secrets.compare_digest(body.username, DEMO_USERNAME)
        and secrets.compare_digest(body.password, DEMO_PASSWORD)
    )
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"token": _issue_token(body.username)}


@router.post("/auth/demo")
def demo_login():
    if not DEMO_AUTH_ENABLED or not DEMO_USERNAME or not DEMO_PASSWORD:
        raise HTTPException(status_code=404, detail="Demo login not enabled")

    return {"token": _issue_token(DEMO_USERNAME)}


@router.get("/auth/check", dependencies=[Depends(require_auth)])
def check_auth():
    return {"status": "ok"}
