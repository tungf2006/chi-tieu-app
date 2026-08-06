from fastapi.testclient import TestClient

from database import Base, engine
from main import app

client = TestClient(app)


def test_full_crud_flow():
    # ensure clean schema for test run
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    txs = [
        {"amount": 10, "category": "Food", "note": "a", "date": "2026-08-06"},
        {"amount": 20, "category": "Transport", "note": "b", "date": "2026-08-06"},
        {"amount": 30, "category": "Food", "note": "c", "date": "2026-08-06"},
        {"amount": 40, "category": "Bills", "note": "d", "date": "2026-08-06"},
        {"amount": 50, "category": "Transport", "note": "e", "date": "2026-08-06"},
    ]

    ids = []
    for t in txs:
        r = client.post("/transactions", json=t)
        assert r.status_code == 200
        ids.append(r.json()["id"])

    # GET list -> should have 5
    r = client.get("/transactions")
    assert r.status_code == 200
    assert len(r.json()) == 5

    # GET one by id -> correct data
    r = client.get(f"/transactions/{ids[2]}")
    assert r.status_code == 200
    data = r.json()
    assert data["amount"] == 30 and data["category"] == "Food"

    # Update one -> changed
    r = client.put(f"/transactions/{ids[0]}", json={"amount": 111})
    assert r.status_code == 200
    assert r.json()["amount"] == 111
    r = client.get(f"/transactions/{ids[0]}")
    assert r.json()["amount"] == 111

    # Delete one -> list length 4
    r = client.delete(f"/transactions/{ids[1]}")
    assert r.status_code == 200
    r = client.get("/transactions")
    assert len(r.json()) == 4
