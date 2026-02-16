"""Customer model - maps to the customers table in Supabase."""

from sqlalchemy import Column, String, Numeric, Date
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    account_number = Column(String, nullable=False, unique=True)
    occupation = Column(String, nullable=True)
    stated_income = Column(Numeric, nullable=True)
    customer_since = Column(Date, nullable=True)

    # Relationships
    transactions = relationship(
        "Transaction", back_populates="customer", lazy="dynamic"
    )
    sar_cases = relationship("SARCase", back_populates="customer", lazy="dynamic")

    def __repr__(self):
        return f"<Customer(name='{self.name}', account='{self.account_number}')>"

    def to_dict(self) -> dict:
        return {
            "customer_id": str(self.customer_id),
            "name": self.name,
            "account_number": self.account_number,
            "occupation": self.occupation,
            "stated_income": float(self.stated_income) if self.stated_income else None,
            "customer_since": str(self.customer_since) if self.customer_since else None,
        }
