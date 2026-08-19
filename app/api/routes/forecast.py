from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import date
import calendar
import pandas as pd

from app.core.database import get_db
from app.models import Transaction
from app.services.forecast import forecast_total

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("")
def forecast_month(
    month: int,
    year: int,
    method: str = "linear",
    db: Session = Depends(get_db),
):
    """
    Dự báo tổng chi tiêu cuối tháng.

    LUU Y: Endpoint nay CHI DOC du lieu tu DB, KHONG co o nhap tien.
    De nhap chi tieu, su dung POST /transactions truoc.

    method:
      - "linear"  : Linear Regression tren cumulative (baseline / burn rate)
      - "seasonal": Tach thu 7, CN cao hon ngay thuong (bat mua vu tuan)
      - "arima"    : ARIMA tren daily amount (bat xu huong tot hon)

    Tra ve: method, predicted_total, burn_rate_per_day, ...
    """
    supported = {"linear", "seasonal", "arima"}
    if method not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"method khong hop le. Chi nhan: {sorted(supported)}",
        )

    rows = (
        db.query(
            Transaction.date,
            func.sum(Transaction.amount).label("y"),
        )
        .filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Không có dữ liệu tháng này để dự báo")

    daily_df = pd.DataFrame([{"ds": r.date, "y": float(r.y)} for r in rows])
    days_in_month = calendar.monthrange(year, month)[1]

    result = forecast_total(
        method=method,
        daily_df=daily_df,
        days_in_month=days_in_month,
        year=year,
        month=month,
        verbose=False,
    )

    result.update({"month": month, "year": year, "days_in_month": days_in_month})
    return result
