"""SAR Narrative model - maps to the sar_narratives table in Supabase."""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class SARNarrative(Base):
    __tablename__ = "sar_narratives"

    narrative_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("sar_cases.case_id"), nullable=True)
    narrative_text = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    generation_time_seconds = Column(Integer, nullable=True)

    # Relationships
    sar_case = relationship("SARCase", back_populates="narratives")
    audit_entries = relationship(
        "AuditTrail", back_populates="narrative", lazy="dynamic"
    )

    def __repr__(self):
        return f"<SARNarrative(id='{self.narrative_id}', case='{self.case_id}')>"

    def to_dict(self) -> dict:
        return {
            "narrative_id": str(self.narrative_id),
            "case_id": str(self.case_id) if self.case_id else None,
            "narrative_text": self.narrative_text,
            "generated_at": self.generated_at.isoformat()
            if self.generated_at
            else None,
            "generation_time_seconds": self.generation_time_seconds,
        }
