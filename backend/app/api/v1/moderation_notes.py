"""
C.O.V.E.R.T - Moderation Notes API

Off-chain notes that moderators attach to reports during deliberation.
One note per (report_id, moderator_address) — upserted on each save.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.models.moderation_note import ModerationNote
from app.api.v1.rbac import require_moderator_role

router = APIRouter(prefix="/moderation/notes", tags=["Moderation Notes"])


class NoteIn(BaseModel):
    moderator_address: str
    content: str


class NoteOut(BaseModel):
    report_id: int
    moderator_address: str
    content: str
    updated_at: str


@router.get("/{report_id}", response_model=List[NoteOut])
async def get_notes(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return all moderator notes for a report."""
    result = await db.execute(
        select(ModerationNote).where(ModerationNote.report_id == report_id)
    )
    notes = result.scalars().all()
    return [
        NoteOut(
            report_id=n.report_id,
            moderator_address=n.moderator_address,
            content=n.content,
            updated_at=n.updated_at.isoformat(),
        )
        for n in notes
    ]


@router.post("/{report_id}", response_model=NoteOut)
async def upsert_note(
    report_id: int,
    body: NoteIn,
    wallet: str = Depends(require_moderator_role),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a moderator's note for a report."""
    result = await db.execute(
        select(ModerationNote).where(
            ModerationNote.report_id == report_id,
            ModerationNote.moderator_address.ilike(body.moderator_address),
        )
    )
    note = result.scalar_one_or_none()

    if note:
        note.content = body.content
    else:
        note = ModerationNote(
            report_id=report_id,
            moderator_address=body.moderator_address.lower(),
            content=body.content,
        )
        db.add(note)

    await db.commit()
    await db.refresh(note)

    return NoteOut(
        report_id=note.report_id,
        moderator_address=note.moderator_address,
        content=note.content,
        updated_at=note.updated_at.isoformat(),
    )


@router.delete("/{report_id}")
async def delete_note(
    report_id: int,
    moderator_address: str,
    wallet: str = Depends(require_moderator_role),
    db: AsyncSession = Depends(get_db),
):
    """Delete a moderator's note for a report."""
    result = await db.execute(
        select(ModerationNote).where(
            ModerationNote.report_id == report_id,
            ModerationNote.moderator_address.ilike(moderator_address),
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    await db.delete(note)
    await db.commit()
    return {"deleted": True}
