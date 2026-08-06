from pydantic import BaseModel
import datetime


class TransactionCreate(BaseModel):
    amount: float | None = None
    category: str | None = None
    note: str | None = None
    date: datetime.date | None = None


class TransactionUpdate(BaseModel):
    amount: float | None = None
    category: str | None = None
    note: str | None = None
    date: datetime.date | None = None

