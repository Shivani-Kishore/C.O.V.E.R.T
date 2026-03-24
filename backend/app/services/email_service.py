"""
C.O.V.E.R.T - Email Notification Service

Sends department notifications using Python built-in smtplib (Gmail SMTP).
No third-party email packages required.
"""

import asyncio
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _send_email_sync(to_email: str, subject: str, body: str) -> None:
    """Synchronous email send via Gmail SMTP. Called in a thread."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.warning("[email] GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set, skipping")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = f"C.O.V.E.R.T Platform <{GMAIL_ADDRESS}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)


async def send_department_notification(dept, report_id, token) -> None:
    """
    Send an initial routing notification to a department.

    Uses asyncio.to_thread to avoid blocking the event loop.
    On failure: logs the error, does not raise.
    """
    if not dept.contact_email:
        logger.info(f"[email] No contact_email for {dept.name}, skipping notification")
        return

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y at %H:%M UTC")
    category = (dept.categories[0] if dept.categories else "general").replace("_", " ").title()

    subject = f"[C.O.V.E.R.T] New Civic Report — {dept.name} | {category}"

    body = f"""Dear {dept.name} Team,

A new anonymous civic report has been submitted on C.O.V.E.R.T and
has been automatically routed to your department.

Category: {category}
Location: Bangalore
Report ID: {report_id}
Submitted on: {date_str}

VIEW FULL REPORT (public):
{FRONTEND_URL}/report/{report_id}

── DEPARTMENT ACTION REQUIRED ──────────────────────────
Update the status of this report using your secure link:
{FRONTEND_URL}/dept-response/{token}

You can mark as: In Progress, Resolved, or No Action.
You may add a public response visible to all citizens.
This link is private to your department.
─────────────────────────────────────────────────────────

Reports are submitted anonymously.
No reporter identity information is available.

— C.O.V.E.R.T Platform
Chain for Open and VERified Testimonies
"""

    try:
        await asyncio.to_thread(_send_email_sync, dept.contact_email, subject, body)
        logger.info(f"[email] Notification sent to {dept.name} ({dept.contact_email})")
    except Exception as e:
        logger.error(f"[email] Failed to send to {dept.name} ({dept.contact_email}): {e}")


async def send_followup_notification(dept, report_id, token, followup_number: int) -> None:
    """
    Send a followup reminder to a non-responsive department.

    Firmer tone. Mentions days elapsed. Does not raise on failure.
    """
    if not dept.contact_email:
        logger.info(f"[email] No contact_email for {dept.name}, skipping followup")
        return

    now = datetime.now(timezone.utc)
    category = (dept.categories[0] if dept.categories else "general").replace("_", " ").title()

    ordinal = "First" if followup_number == 1 else "Second"

    subject = f"[REMINDER {followup_number}] Pending Civic Report — {dept.name}"

    body = f"""Dear {dept.name} Team,

This is the {ordinal.lower()} reminder regarding an unresolved civic report
that was routed to your department on C.O.V.E.R.T.

Category: {category}
Location: Bangalore
Report ID: {report_id}

Your department has not yet responded to this report.
Please note that the report is publicly visible and currently shows
your department's status as PENDING (no response).

── RESPOND NOW ─────────────────────────────────────────
{FRONTEND_URL}/dept-response/{token}

Mark as: In Progress, Resolved, or No Action.
Add a public response visible to all citizens.
─────────────────────────────────────────────────────────

Timely responses build public trust in civic institutions.

— C.O.V.E.R.T Platform
Chain for Open and VERified Testimonies
"""

    try:
        await asyncio.to_thread(_send_email_sync, dept.contact_email, subject, body)
        logger.info(
            f"[email] Followup {followup_number} sent to {dept.name} ({dept.contact_email})"
        )
    except Exception as e:
        logger.error(
            f"[email] Failed followup {followup_number} to {dept.name} ({dept.contact_email}): {e}"
        )
