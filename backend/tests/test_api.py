import os
import pytest
from httpx import ASGITransport, AsyncClient
from app.db.session import Base, engine, SessionLocal
from app.models import Currency

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_buyerflow.db"
from app.main import app


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if not (await db.execute(__import__("sqlalchemy").select(Currency))).first():
            db.add(Currency(code="USD", name="Dollar", base_rate=100, markup_percent=20))
            await db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    assert (await client.get("/health/live")).json()["status"] == "ok"
    assert (await client.get("/health/ready")).status_code == 200


@pytest.mark.asyncio
async def test_login_and_quote(client):
    assert (await client.post("/api/v1/auth/login", json={"username": "admin", "password": "change-me"})).status_code == 200
    response = await client.post(
        "/api/v1/calculator/quote",
        json={
            "country": "США",
            "product_url": "https://example.com/item",
            "product_name": "Test",
            "price": 10,
            "currency": "USD",
            "quantity": 1,
        },
    )
    assert response.status_code == 200 and response.json()["rate"] == "120.00"
    assert "bot" not in response.text.lower()


@pytest.mark.asyncio
async def test_validation(client):
    bad = await client.post(
        "/api/v1/calculator/quote",
        json={"country": "США", "product_url": "http://127.0.0.1/x", "product_name": "x", "price": -1, "currency": "USD", "quantity": 0},
    )
    assert bad.status_code == 422
