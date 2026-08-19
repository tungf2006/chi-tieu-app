from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category")
    note = Column(String(255), default="")
    date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)