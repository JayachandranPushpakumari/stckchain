import importlib
import os

import pandas as pd
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["APP_USERNAME"] = "test-user"
os.environ["APP_PASSWORD"] = "test-password"
os.environ["TOKEN_SECRET"] = "test-token-secret"
os.environ["ENABLE_DEMO_AUTH"] = "false"

main = importlib.import_module("main")
swing = importlib.import_module("routes.swing")
client = TestClient(main.app)


def auth_headers():
    response = client.post("/auth/login", json={"username": "test-user", "password": "test-password"})
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_data_routes_require_authentication():
    for path in ("/signals/RELIANCE", "/scan", "/screen/swing"):
        assert client.get(path).status_code == 401


def test_signal_route(monkeypatch):
    prices = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=60), "close": range(100, 160)})
    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: prices.copy())
    response = client.get("/signals/RELIANCE", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["signal"] == "BUY"


def test_scan_route(monkeypatch):
    rows = []
    for index in range(60):
        rows.append({"date": pd.Timestamp("2025-01-01") + pd.Timedelta(days=index), "symbol": "TEST", "close": 100 - index})
    monkeypatch.setattr(pd, "read_sql", lambda *args, **kwargs: pd.DataFrame(rows))
    response = client.get("/scan", headers=auth_headers())
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_swing_route(monkeypatch):
    monkeypatch.setattr(swing, "calculate_fundamental_score", lambda save_to_db=False: {"symbols": []})
    response = client.get("/screen/swing", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"symbols": []}
