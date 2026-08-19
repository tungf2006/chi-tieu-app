# Chi Tieu App

A small FastAPI app for tracking simple transactions using SQLite.

## Tech Stack
- FastAPI
- SQLAlchemy
- SQLite
- Pandas (báo cáo & groupby)
- Matplotlib (biểu đồ pie chart)
- Scikit-learn (Linear Regression)
- Statsmodels (ARIMA)

## Project Structure
```
chi-tieu-app/
├── app/
│   ├── __init__.py
│   ├── main.py                 # App factory & entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── database.py         # DB engine, session, Base
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py           # Transaction, Category models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── categorize.py       # Auto-categorize logic
│   │   ├── reports.py          # Report generation & charts
│   │   └── forecast.py         # Forecast: linear / seasonal / arima
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── transactions.py # Transaction CRUD, filter & clear
│           ├── categories.py   # Category CRUD
│           ├── reports.py       # Monthly report & chart
│           └── forecast.py      # Forecast endpoint (method selector)
├── alembic/                    # Database migrations
├── tests/                      # Test files
├── requirements.txt
├── README.md
├── .gitignore
├── alembic.ini
└── main.py                     # Entry point (runs app)
```

## Prerequisites
- Python 3.10+
- Install dependencies:

```powershell
pip install -r requirements.txt
```

## What it does
- Create, read, update, delete transactions
- Auto-categorize transactions by note (regex)
- Filter transactions by category / month / year
- Monthly spending report grouped by category
- Pie chart visualization of monthly spending
- **Forecast** month-end total spending (Linear / Seasonal / ARIMA)
- Uses SQLite (`chi-tieu.db`) and SQLAlchemy

## Run locally
1. Activate your virtualenv

```powershell
venv\Scripts\activate
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Start the app

```powershell
uvicorn main:app --reload
```

Or run directly:
```powershell
python main.py
```

## API Docs
Once the server is running, interactive API documentation (Swagger UI) is available at:
- `http://127.0.0.1:8000/docs`

## Endpoints

### Transactions
- `POST /transactions` — create a transaction (auto-categorize if no category_id)
- `GET /transactions` — list all transactions
- `GET /transactions/filter?category_id=1&month=8&year=2026` — filter by category/month/year
- `GET /transactions/{id}` — get one transaction
- `PUT /transactions/{id}` — update a transaction (partial updates)
- `DELETE /transactions/{id}` — delete a transaction

### Categories
- `POST /categories` — create a category
- `GET /categories` — list all categories

### Reports
- `GET /reports/monthly?month=8&year=2026` — monthly spending summary grouped by category
- `GET /reports/monthly/chart?month=8&year=2026` — pie chart image (PNG) of monthly spending

### Forecast
- `GET /forecast?month=8&year=2026&method=linear` — dự báo tổng chi tiêu cuối tháng
  - `method=linear`  : Linear Regression trên chuỗi tích lũy (baseline / burn rate)
  - `method=seasonal`: tách T7-CN, bắt mùa vụ tuần (MAPE thấp nhất với data có chu kỳ)
  - `method=arima`    : ARIMA trên daily amount, bắt xu hướng tăng/giảm tốt nhất

### Data management
- `DELETE /transactions/clear` — xóa TOÀN BỘ giao dịch (reset DB giữa các lần test)
- `DELETE /transactions?month=8&year=2026` — xóa giao dịch theo tháng/năm

## Tests
Run unit tests:

```powershell
python -m pytest tests/ -q
```

Run integration tests (requires server running on port 8000):

```powershell
python tests/test_all_endpoints.py
```

Test auto-categorize:

```powershell
python tests/test_autocat.py
```

## Key Concepts (Phase 2)
- **Foreign Key**: `Transaction.category_id` → `Category.id` (mối quan hệ 1-n)
- **Migration**: Alembic quản lý schema thay vì `create_all()`
- **GroupBy**: Pandas `df.groupby("category")["amount"].sum()` tổng hợp theo nhóm
- **StreamingResponse**: Trả về binary stream (ảnh PNG) thay vì JSON

## Key Concepts (Phase 3 — Forecasting)
- **Time-series**: dữ liệu index theo thời gian, giá trị hiện tại phụ thuộc quá khứ (temporal dependency)
- **Cumulative sum**: tổng tích lũy giúp làm mượt nhiễu, fit tuyến tính ổn định hơn daily amount
- **Burn rate**: độ dốc (slope) của đường cumulative = tốc độ chi tiêu trung bình/ngày
- **Linear Regression**: `y = slope·day + intercept` → ngoại suy tổng cuối tháng
- **Seasonality**: mùa vụ tuần (cuối tuần cao hơn) → tách T7/CN để dự báo chính xác hơn
- **ARIMA**: `(p,d,q)` với `d=1` (differencing) bắt xu hướng tăng/giảm; tốt cho TC3/TC5
- **MAPE**: Mean Absolute Percentage Error — thước đo độ chính xác dự báo
- **Outlier / IQR**: điểm bất thường phi chu kỳ làm lệch trend → phát hiện bằng IQR `[Q1−1.5·IQR, Q3+1.5·IQR]`
- **Moving Average**: trung bình trượt 7 ngày tăng độ nhạy với biến động gần nhất

### Kết quả đo (8 datasets, so sánh 3 method)
| Dataset | Linear | Seasonal | ARIMA |
|---------|--------|----------|-------|
| TC1 PerfectLinear | 0.0% | 0.0% | 0.0% |
| TC2 WeeklySeasonality | 1.9% | **0.0%** | 14.4% |
| TC3 IncreasingTrend | 15.9% | 13.7% | **0.1%** |
| TC5 DecreasingTrend | 25.5% | 22.0% | **0.3%** |
| TC4 Outlier | 24.1% | 25.5% | 156.7%* |

\* ARIMA nhạy cảm với outlier/ít dữ liệu → cần làm sạch (IQR) trước khi fit.
Chi tiết: `docs/SOP_DAY30_Compare_Tune.md`, `tests/test_forecast_scenarios.py`.

## Postman
A sample Postman collection is provided at `postman_collection.json`.