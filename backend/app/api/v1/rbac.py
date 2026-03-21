"""
C.O.V.E.R.T - Role-Based Access Control Dependencies

FastAPI dependencies that verify on-chain roles (REVIEWER_ROLE, MODERATOR_ROLE)
by calling the CovertProtocol smart contract via Web3.py.

Usage:
    @router.get("/some-endpoint")
    async def endpoint(wallet: str = Depends(require_reviewer_role)):
        ...
"""

import logging

from fastapi import Depends, HTTPException, status

from app.api.v1.auth import get_current_wallet
from app.services.blockchain_service import blockchain_service
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _ensure_blockchain_ready() -> None:
    """Initialize blockchain service if not yet connected."""
    if not blockchain_service.w3:
        try:
            await blockchain_service.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Blockchain service unavailable",
            )


async def require_reviewer_role(
    wallet: str = Depends(get_current_wallet),
) -> str:
    """
    Verify the authenticated wallet holds REVIEWER_ROLE on-chain.
    Returns the wallet address if authorized.
    """
    # In dev mode without contract deployment, fall back to config-based role check
    if (settings.ENVIRONMENT == "development" and settings.DEBUG) and not settings.COVERT_PROTOCOL_ADDRESS:
        return wallet

    await _ensure_blockchain_ready()

    has_role = await blockchain_service.has_reviewer_role(wallet)
    if not has_role:
        # Also check moderator role — moderators can do everything reviewers can
        has_mod = await blockchain_service.has_moderator_role(wallet) if hasattr(blockchain_service, 'has_moderator_role') else False
        if not has_mod:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="REVIEWER_ROLE required",
            )

    return wallet


async def require_moderator_role(
    wallet: str = Depends(get_current_wallet),
) -> str:
    """
    Verify the authenticated wallet holds MODERATOR_ROLE on-chain.
    Returns the wallet address if authorized.
    """
    if (settings.ENVIRONMENT == "development" and settings.DEBUG) and not settings.COVERT_PROTOCOL_ADDRESS:
        return wallet

    await _ensure_blockchain_ready()

    has_role = await blockchain_service.has_moderator_role(wallet) if hasattr(blockchain_service, 'has_moderator_role') else False
    if not has_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MODERATOR_ROLE required",
        )

    return wallet
