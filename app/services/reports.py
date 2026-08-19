import io
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from fastapi.responses import StreamingResponse


def create_pie_chart(summary: dict) -> io.BytesIO:
    """Tạo biểu đồ tròn từ dữ liệu summary, trả về BytesIO buffer."""
    fig, ax = plt.subplots()
    ax.pie(summary.values(), labels=summary.keys(), autopct="%1.1f%%")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_monthly_summary(transactions) -> dict:
    """Tạo summary báo cáo tháng từ list transactions."""
    data = [
        {"category": t.category.name if t.category else "Khác", "amount": t.amount}
        for t in transactions
    ]
    if not data:
        return {}
    df = pd.DataFrame(data)
    return df.groupby("category")["amount"].sum().to_dict()