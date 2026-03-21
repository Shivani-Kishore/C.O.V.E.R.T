"""
C.O.V.E.R.T - Celery Worker Configuration

Periodic tasks:
  - dms-watchdog: every 30 minutes — checks for triggered Dead Man's Switches
  - sync-reviewer-roles: every 6 hours — grants/revokes REVIEWER_ROLE on-chain

Start with:
  celery -A app.celery_app worker --beat --loglevel=info
"""

import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Celery app ───────────────────────────────────────────────────────────────
celery = Celery(
    "covert",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# ── Beat schedule ────────────────────────────────────────────────────────────
celery.conf.beat_schedule = {
    "dms-watchdog": {
        "task": "app.celery_app.dms_watchdog_task",
        "schedule": 30 * 60,  # every 30 minutes
    },
    "sync-reviewer-roles": {
        "task": "app.celery_app.sync_reviewer_roles_task",
        "schedule": 6 * 60 * 60,  # every 6 hours
    },
}


# ── Tasks ────────────────────────────────────────────────────────────────────

@celery.task(name="app.celery_app.dms_watchdog_task")
def dms_watchdog_task():
    """
    Check for DMS entries whose trigger date has passed and release them.

    Runs the watchdog service's manual_trigger_check in a sync context
    by creating a fresh async event loop (Celery workers are sync by default).
    """
    import asyncio
    from app.core.database import async_session_maker
    from app.services.dms import watchdog_service

    async def _run():
        async with async_session_maker() as db:
            result = await watchdog_service.manual_trigger_check(db)
            logger.info(f"[celery] DMS watchdog: {result}")
            return result

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()


@celery.task(name="app.celery_app.sync_reviewer_roles_task")
def sync_reviewer_roles_task():
    """
    Scan eligible wallets and grant/revoke REVIEWER_ROLE on-chain.

    Requires AUTOMATION_PRIVATE_KEY and COVERT_PROTOCOL_ADDRESS in env.
    """
    if not settings.AUTOMATION_PRIVATE_KEY or not settings.COVERT_PROTOCOL_ADDRESS:
        logger.warning(
            "[celery] sync-reviewer-roles skipped: "
            "AUTOMATION_PRIVATE_KEY or COVERT_PROTOCOL_ADDRESS not set"
        )
        return {"skipped": True}

    import asyncio
    from app.core.database import async_session_maker
    from app.services.reputation_service import reputation_service
    from app.services.blockchain_service import blockchain_service

    async def _run():
        if not blockchain_service.w3:
            await blockchain_service.initialize()

        async with async_session_maker() as db:
            candidates = await reputation_service.get_reviewer_candidates(db, limit=100)
            granted, revoked, errors = [], [], []

            for candidate in candidates:
                wallet = candidate["wallet_address"]
                eligibility = await reputation_service.check_reviewer_eligibility(db, wallet)
                has_role = await blockchain_service.has_reviewer_role(wallet)

                try:
                    if eligibility["eligible"] and not has_role:
                        await blockchain_service.grant_reviewer_role(wallet)
                        granted.append(wallet)
                    elif not eligibility["eligible"] and has_role:
                        await blockchain_service.revoke_reviewer_role(wallet)
                        revoked.append(wallet)
                except Exception as e:
                    errors.append({"wallet": wallet, "error": str(e)})

            result = {
                "granted": granted,
                "revoked": revoked,
                "errors": errors,
                "scanned": len(candidates),
            }
            logger.info(f"[celery] sync-reviewer-roles: {result}")
            return result

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run())
        finally:
            loop.close()
