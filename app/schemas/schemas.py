from pydantic import BaseModel
from datetime import date
import datetime


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    amount: float
    category_id: int | None = None
    note: str = ""
    date: date


class TransactionUpdate(BaseModel):
    amount: float | None = None
    category_id: int | None = None
    note: str | None = None
    date: datetime.date | None = None


