"""
C.O.V.E.R.T - Dev-only reset endpoint.
Only available when DEBUG=true or ENVIRONMENT=development.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings
from app.services.reputation_service import reputation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["Dev"])


def _require_dev():
    if not (settings.DEBUG and settings.ENVIRONMENT == "development"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode.",
        )


@router.post("/reset-all")
async def dev_reset_all(db: AsyncSession = Depends(get_db)):
    """
    Full dev reset: wipes all reports, reputation, and moderator data from the DB.
    Call this after restarting Anvil + redeploying contracts to get a clean slate.

    Only available when DEBUG=true or ENVIRONMENT=development.
    """
    _require_dev()

    counts: dict = {}

    # Cascade-safe deletion order: child tables first, then parents
    tables = [
        "moderation_notes",
        "moderation_logs",
        "moderations",
        "zkp_nullifiers",
        "dms_messages",
        "dms_channels",
        "reports",
        "user_reputation",
        "moderators",
    ]

    for table in tables:
        try:
            result = await db.execute(text(f"DELETE FROM {table}"))
            counts[table] = result.rowcount
        except Exception as exc:
            # Table may not exist (optional features) — log and continue
            logger.warning(f"[dev-reset] Could not clear {table}: {exc}")
            counts[table] = "skipped"

    await db.commit()

    # Re-seed reputation scores for known test accounts so they start with
    # role-appropriate rep (users=0, reviewers=50, moderators=90).
    seed_result = await reputation_service.seed_dev_accounts(db)

    logger.info(f"[dev-reset] Reset complete: {counts}")
    return {
        "success": True,
        "message": (
            "DB cleared and rep re-seeded. "
            "For a full reset also run: forge script script/Reset.s.sol --rpc-url localhost --broadcast"
        ),
        "cleared": counts,
        "reputation_seeded": seed_result["seeded"],
    }
