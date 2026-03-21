"""
C.O.V.E.R.T - EIP-4361 Sign-In with Ethereum (SIWE) Authentication

Provides:
  - GET  /auth/nonce?address=0x...  → returns a random nonce
  - POST /auth/verify               → verifies signed SIWE message, returns JWT
  - Dependency: get_current_wallet   → validates JWT on protected routes
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from jose import jwt, JWTError
from siwe import SiweMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── In-memory nonce store (use Redis in production) ──────────────────────────
# Maps lowercase wallet address → nonce string.
# In production, replace with Redis using settings.REDIS_URL for horizontal scaling.
_nonce_store: dict[str, str] = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class NonceResponse(BaseModel):
    nonce: str


class VerifyRequest(BaseModel):
    message: str   # The full EIP-4361 plaintext message the user signed
    signature: str  # The wallet's hex signature (0x-prefixed)


class VerifyResponse(BaseModel):
    token: str
    address: str
    expires_at: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/nonce", response_model=NonceResponse)
async def get_nonce(address: str = Query(..., min_length=42, max_length=42)):
    """Generate and store a random nonce for the given wallet address."""
    key = address.lower()
    nonce = secrets.token_hex(16)
    _nonce_store[key] = nonce
    return NonceResponse(nonce=nonce)


@router.post("/verify", response_model=VerifyResponse)
async def verify_signature(body: VerifyRequest):
    """
    Verify a signed EIP-4361 (SIWE) message and return a JWT.

    The frontend constructs the SIWE message using the nonce from /auth/nonce,
    asks the wallet to sign it, then sends both here.
    """
    try:
        siwe_message = SiweMessage.from_message(body.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid SIWE message format: {e}",
        )

    address_key = siwe_message.address.lower()

    # Verify nonce matches the one we issued
    expected_nonce = _nonce_store.pop(address_key, None)
    if expected_nonce is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No nonce issued for this address. Call /auth/nonce first.",
        )
    if siwe_message.nonce != expected_nonce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nonce mismatch.",
        )

    # Verify the cryptographic signature
    try:
        siwe_message.verify(body.signature)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Signature verification failed: {e}",
        )

    # Issue JWT
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": address_key,
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return VerifyResponse(
        token=token,
        address=address_key,
        expires_at=expires_at.isoformat(),
    )


# ── Dependency: extract and validate wallet from JWT ─────────────────────────

async def get_current_wallet(request: Request) -> str:
    """
    FastAPI dependency that extracts the authenticated wallet address from
    the Authorization header (Bearer JWT).

    Returns the lowercase wallet address.
    Raises 401 if the token is missing, expired, or invalid.
    """
    # In development mode, fall back to X-Wallet-Address header for backwards compat
    # Both flags must be true to prevent accidental bypass in production
    if settings.ENVIRONMENT == "development" and settings.DEBUG:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Fallback: trust X-Wallet-Address in dev mode
            wallet = request.headers.get("X-Wallet-Address")
            if wallet:
                return wallet.lower()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        wallet_address: Optional[str] = payload.get("sub")
        if wallet_address is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return wallet_address.lower()
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_wallet(request: Request) -> Optional[str]:
    """
    Like get_current_wallet but returns None instead of raising 401.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    try:
        return await get_current_wallet(request)
    except HTTPException:
        return None
