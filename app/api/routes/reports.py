from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.models import Transaction
from app.services.reports import create_pie_chart, generate_monthly_summary

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly")
def monthly_report(month: int, year: int, db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .filter(
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        .all()
    )

    summary = generate_monthly_summary(transactions)
    if not summary:
        return {"message": "Không có dữ liệu tháng này"}

    return {"month": month, "year": year, "summary": summary}


@router.get("/monthly/chart")
def monthly_report_chart(month: int, year: int, db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .filter(
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        .all()
    )

    summary = generate_monthly_summary(transactions)
    if not summary:
        raise HTTPException(status_code=404, detail="Không có dữ liệu tháng này")

    buf = create_pie_chart(summary)
    return StreamingResponse(buf, media_type="image/png")