from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
import models
from main import app

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_update_transaction_and_get_it_back():
    create_response = client.post(
        "/transactions",
        json={"amount": 100, "category": "Food", "note": "Lunch", "date": "2026-08-06"},
    )
    assert create_response.status_code == 200
    transaction_id = create_response.json()["id"]

    update_response = client.put(
        f"/transactions/{transaction_id}",
        json={"amount": 250},
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == 250

    get_response = client.get(f"/transactions/{transaction_id}")
    assert get_response.status_code == 200
    assert get_response.json()["amount"] == 250
