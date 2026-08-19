from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
import pandas as pd
import io
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from fastapi.responses import StreamingResponse

from database import Base, SessionLocal, engine


import re

def auto_categorize(note: str) -> str:
    note = note.lower()
    # Use regex word boundaries for accurate matching
    an_uong_patterns = [r"\ban\b", r"cơm|com", r"trà sữa|tra sua", r"cafe"]
    hoc_tap_patterns = [r"sách|sach", r"học phí|hoc phi", r"khóa học|khoa hoc"]
    mua_sam_patterns = [r"quần áo|quan ao", r"giày|giay", r"mua sắm|mua sam"]
    
    if any(re.search(p, note) for p in an_uong_patterns):
        return "An uong"
    if any(re.search(p, note) for p in hoc_tap_patterns):
        return "Hoc tap"
    if any(re.search(p, note) for p in mua_sam_patterns):
        return "Mua sam"
    return "Khac"
import models
import schemas

app = FastAPI()

# Hàm cấp session DB cho mỗi request, tự đóng lại sau khi xong
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/transactions")
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # Auto-categorize if category_id not provided but note exists
    category_id = transaction.category_id
    if category_id is None and transaction.note:
        category_name = auto_categorize(transaction.note)
        category = db.query(models.Category).filter(models.Category.name == category_name).first()
        if not category:
            category = models.Category(name=category_name)
            db.add(category)
            db.commit()
            db.refresh(category)
        category_id = category.id

    new_transaction = models.Transaction(
        amount=transaction.amount,
        category_id=category_id,
        note=transaction.note,
        date=transaction.date
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@app.get("/transactions")
def list_transactions(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()
    return transactions


@app.get("/transactions/filter")
def filter_transactions(
    category_id: int | None = None,
    month: int | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transaction)
    if category_id is not None:
        query = query.filter(models.Transaction.category_id == category_id)
    if month is not None:
        query = query.filter(extract("month", models.Transaction.date) == month)
    if year is not None:
        query = query.filter(extract("year", models.Transaction.date) == year)
    return query.all()


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")
    return transaction


@app.put("/transactions/{transaction_id}")
def update_transaction(transaction_id: int, data: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(transaction, key, value)

    db.commit()
    db.refresh(transaction)
    return transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch")

    db.delete(transaction)
    db.commit()
    return {"message": "Giao dịch đã được xóa"}

@app.post("/categories", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    new_category = models.Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.get("/categories", response_model=list[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


@app.get("/reports/monthly")
def monthly_report(month: int, year: int, db: Session = Depends(get_db)):
    transactions = (
        db.query(models.Transaction)
        .filter(
            extract("month", models.Transaction.date) == month,
            extract("year", models.Transaction.date) == year,
        )
        .all()
    )

    data = [
        {"category": t.category.name if t.category else "Khác", "amount": t.amount}
        for t in transactions
    ]
    if not data:
        return {"message": "Không có dữ liệu tháng này"}

    df = pd.DataFrame(data)
    summary = df.groupby("category")["amount"].sum().to_dict()
    return {"month": month, "year": year, "summary": summary}


def create_pie_chart(summary: dict):
    fig, ax = plt.subplots()
    ax.pie(summary.values(), labels=summary.keys(), autopct="%1.1f%%")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf


@app.get("/reports/monthly/chart")
def monthly_report_chart(month: int, year: int, db: Session = Depends(get_db)):
    transactions = (
        db.query(models.Transaction)
        .filter(
            extract("month", models.Transaction.date) == month,
            extract("year", models.Transaction.date) == year,
        )
        .all()
    )

    data = [
        {"category": t.category.name if t.category else "Khác", "amount": t.amount}
        for t in transactions
    ]
    if not data:
        raise HTTPException(status_code=404, detail="Không có dữ liệu tháng này")

    df = pd.DataFrame(data)
    summary = df.groupby("category")["amount"].sum().to_dict()

    buf = create_pie_chart(summary)
    return StreamingResponse(buf, media_type="image/png")