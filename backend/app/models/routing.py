"""
C.O.V.E.R.T - Department & Report Routing Models
"""

import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Department(Base):
    """City department that can receive routed civic reports."""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=True)
    jurisdiction_city = Column(String, server_default="Bangalore")
    categories = Column(ARRAY(String), nullable=True)
    contact_email = Column(String, nullable=True)
    is_active = Column(Boolean, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    routings = relationship("ReportRouting", back_populates="department")

    def __repr__(self):
        return f"<Department {self.short_name or self.name}>"


class ReportRouting(Base):
    """Tracks which department a report has been routed to and their response."""
    __tablename__ = "report_routing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    routed_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_sent = Column(Boolean, server_default="false")
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, server_default="PENDING")
    department_response = Column(Text, nullable=True)
    response_token = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    followup_count = Column(Integer, server_default="0")
    last_followup_at = Column(DateTime(timezone=True), nullable=True)

    department = relationship("Department", back_populates="routings")

    __table_args__ = (
        Index("idx_report_routing_report", "report_id"),
        Index("idx_report_routing_dept", "department_id"),
    )

    def __repr__(self):
        return f"<ReportRouting {self.id} status={self.status}>"
