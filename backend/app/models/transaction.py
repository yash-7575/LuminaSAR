"""Transaction model - maps to the transactions table in Supabase."""

from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=True)
    amount = Column(Numeric, nullable=False)
    date = Column(DateTime, nullable=True, default=datetime.utcnow)
    source_account = Column(String, nullable=True)
    destination_account = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id='{self.transaction_id}', amount={self.amount})>"

    def to_dict(self) -> dict:
        return {
            "transaction_id": str(self.transaction_id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "amount": float(self.amount),
            "date": self.date.isoformat() if self.date else None,
            "source_account": self.source_account,
            "destination_account": self.destination_account,
            "transaction_type": self.transaction_type,
        }
