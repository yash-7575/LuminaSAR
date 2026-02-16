"""SAR Case model - maps to the sar_cases table in Supabase."""

from sqlalchemy import Column, String, Numeric, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class SARCase(Base):
    __tablename__ = "sar_cases"

    case_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=True)
    status = Column(String, nullable=True, default="pending")
    risk_score = Column(Numeric, nullable=True)
    typologies = Column(JSON, nullable=True, default=[])
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="sar_cases")
    narratives = relationship("SARNarrative", back_populates="sar_case", lazy="dynamic")

    def __repr__(self):
        return f"<SARCase(id='{self.case_id}', status='{self.status}')>"

    def to_dict(self) -> dict:
        return {
            "case_id": str(self.case_id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "status": self.status,
            "risk_score": float(self.risk_score) if self.risk_score else None,
            "typologies": self.typologies or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
