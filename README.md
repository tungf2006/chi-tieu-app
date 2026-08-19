# Chi Tieu App

A small FastAPI app for tracking simple transactions using SQLite.

## Tech Stack
- FastAPI
- SQLAlchemy
- SQLite
- Pandas (báo cáo & groupby)
- Matplotlib (biểu đồ pie chart)

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
│   │   └── reports.py          # Report generation & charts
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── transactions.py # Transaction CRUD & filter
│           ├── categories.py   # Category CRUD
│           └── reports.py      # Monthly report & chart
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

## Postman
A sample Postman collection is provided at `postman_collection.json`.