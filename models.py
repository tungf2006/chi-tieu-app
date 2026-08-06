from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String

from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50))
    note = Column(String(255), default="")
    date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)