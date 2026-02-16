"""Audit Trail model - maps to the audit_trail table in Supabase."""

from sqlalchemy import Column, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    audit_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    narrative_id = Column(
        String, ForeignKey("sar_narratives.narrative_id"), nullable=True
    )
    step_name = Column(String, nullable=False)
    data_sources = Column(JSON, nullable=True, default={})
    reasoning = Column(JSON, nullable=True, default={})
    confidence_scores = Column(JSON, nullable=True, default={})
    logged_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    previous_hash = Column(String, nullable=True)
    current_hash = Column(String, nullable=True)

    # Relationships
    narrative = relationship("SARNarrative", back_populates="audit_entries")

    def __repr__(self):
        return (
            f"<AuditTrail(step='{self.step_name}', hash='{self.current_hash[:8]}...')>"
        )

    def to_dict(self) -> dict:
        return {
            "audit_id": str(self.audit_id),
            "narrative_id": str(self.narrative_id) if self.narrative_id else None,
            "step_name": self.step_name,
            "data_sources": self.data_sources or {},
            "reasoning": self.reasoning or {},
            "confidence_scores": self.confidence_scores or {},
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
        }
