# Chi Tieu App

A small FastAPI app for tracking simple transactions using SQLite.

## What it does
- Create, read, update, delete transactions
- Uses SQLite (`chi_tieu.db`) and SQLAlchemy

## Run locally
1. Activate your virtualenv

```powershell
venv\Scripts\activate
```

2. Start the app

```powershell
uvicorn main:app --reload
```

## Endpoints
- `POST /transactions` — create a transaction
- `GET /transactions` — list all transactions
- `GET /transactions/{id}` — get one transaction
- `PUT /transactions/{id}` — update a transaction (partial updates supported)
- `DELETE /transactions/{id}` — delete a transaction

## Tests
Run:

```powershell
python -m pytest -q
```

## Postman
A sample Postman collection is provided at `postman_collection.json`.

## Commit
Commit message used when committing locally: `feat: hoàn thành CRUD transactions với FastAPI + SQLite`