"""
C.O.V.E.R.T - ModerationNote Model

Stores off-chain notes that moderators attach to reports during deliberation.
One note per (report_id, moderator_address) pair — upserted on save.
"""

import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ModerationNote(Base):
    __tablename__ = "moderation_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(Integer, nullable=False, index=True)
    moderator_address = Column(String(42), nullable=False)
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "report_id", "moderator_address",
            name="uq_note_report_moderator",
        ),
    )

    def __repr__(self):
        return f"<ModerationNote report={self.report_id} mod={self.moderator_address}>"
