from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.core.database import get_db
from app.models import Transaction, Category
from app.schemas import TransactionCreate, TransactionUpdate
from app.services.categorize import auto_categorize

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=None)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    category_id = transaction.category_id
    if category_id is None and transaction.note:
        category_name = auto_categorize(transaction.note)
        category = db.query(Category).filter(Category.name == category_name).first()
        if not category:
            category = Category(name=category_name)
            db.add(category)
            db.commit()
            db.refresh(category)
        category_id = category.id

    new_transaction = Transaction(
        amount=transaction.amount,
        category_id=category_id,
        note=transaction.note,
        date=transaction.date,
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@router.get("")
def list_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()


@router.delete("/clear")
def clear_all_transactions(db: Session = Depends(get_db)):
    """Xoa TOAN BO giao dich (dung de reset DB giua cac lan test)."""
    deleted = db.query(Transaction).delete()
    db.commit()
    return {"message": f"Da xoa {deleted} giao dich", "deleted": deleted}


@router.delete("")
def delete_transactions_by_filter(
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    """Xoa giao dich theo thang/nam (loc tuy chon)."""
    query = db.query(Transaction)
    if month is not None:
        query = query.filter(extract("month", Transaction.date) == month)
    if year is not None:
        query = query.filter(extract("year", Transaction.date) == year)
    deleted = query.delete()
    db.commit()
    return {"message": f"Da xoa {deleted} giao dich", "deleted": deleted}


@router.get("/filter")
def filter_transactions(
    category_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if month is not None:
        query = query.filter(extract("month", Transaction.date) == month)
    if year is not None:
        query = query.filter(extract("year", Transaction.date) == year)
    return query.all()


@router.get("/{transaction_id}")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")
    return transaction


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int, data: TransactionUpdate, db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")

    db.delete(transaction)
    db.commit()
    return {"message": "Giao dịch đã được xóa"}