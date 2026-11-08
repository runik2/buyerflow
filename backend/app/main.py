import csv
import io
import secrets
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_token, current_admin
from app.db.session import Base, engine, get_db
from app.models import AuditLog, Currency, OrderRequest, ShippingRate, Store
from app.schemas.common import (
    CurrencyIn,
    CurrencyOut,
    LoginIn,
    MeOut,
    OrderIn,
    OrderOut,
    OrderPatch,
    QuoteIn,
    QuoteOut,
    ShippingIn,
    ShippingOut,
    StoreIn,
    StoreOut,
    TokenOut,
)
from app.services.calculator import quote
from app.services.notifications import TelegramNotificationService

STATUSES = {
    "new",
    "calculating",
    "calculated",
    "awaiting_payment",
    "purchased",
    "warehouse",
    "shipped",
    "delivered",
    "cancelled",
    "needs_review",
}


@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as db:
        if not (await db.execute(select(Currency))).first():
            db.add_all(
                [
                    Currency(code=c, name=n, base_rate=r, markup_percent=20)
                    for c, n, r in [
                        ("USD", "Доллар США", 100),
                        ("EUR", "Евро", 108),
                        ("GBP", "Фунт стерлингов", 128),
                        ("CNY", "Юань", 14),
                        ("TRY", "Турецкая лира", 3),
                    ]
                ]
            )
            db.add_all(
                [
                    Store(name=n, country=c, category=cat, url=u, description="demo/seed data", logo="🛍️", sort_priority=1)
                    for n, c, cat, u in [
                        ("Amazon", "США", "Электроника", "https://www.amazon.com"),
                        ("eBay", "США", "Другое", "https://www.ebay.com"),
                        ("Nike", "США", "Одежда", "https://www.nike.com"),
                        ("Adidas", "Германия", "Спорт", "https://www.adidas.com"),
                        ("Zalando", "Европа", "Обувь", "https://www.zalando.com"),
                        ("ASOS", "Великобритания", "Одежда", "https://www.asos.com"),
                        ("Farfetch", "Великобритания", "Люкс", "https://www.farfetch.com"),
                        ("Walmart", "США", "Товары для дома", "https://www.walmart.com"),
                        ("Sephora", "Франция", "Косметика", "https://www.sephora.com"),
                    ]
                ]
            )
            await db.commit()
    yield


app = FastAPI(title="BuyerFlow API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health/live")
async def live():
    return {"status": "ok"}


@app.get("/health/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    await db.execute(select(1))
    return {"status": "ready"}


@app.post("/api/v1/auth/login", response_model=TokenOut)
async def login(data: LoginIn):
    if data.username != settings.admin_username or data.password != settings.admin_password:
        raise HTTPException(401, "Неверные данные")
    return TokenOut(access_token=create_token(data.username))


@app.get("/api/v1/auth/me", response_model=MeOut)
async def me(user=Depends(current_admin)):
    return MeOut(username=user)


def protected(user=Depends(current_admin)):
    return user


@app.get("/api/v1/currencies", response_model=list[CurrencyOut])
async def currencies(db=Depends(get_db)):
    return (await db.execute(select(Currency).order_by(Currency.code))).scalars().all()


@app.post("/api/v1/currencies", response_model=CurrencyOut)
async def add_currency(data: CurrencyIn, db=Depends(get_db), _=Depends(protected)):
    item = Currency(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@app.patch("/api/v1/currencies/{id}", response_model=CurrencyOut)
async def edit_currency(id: int, data: CurrencyIn, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(Currency, id)
    if not item:
        raise HTTPException(404, "Валюта не найдена")
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


@app.delete("/api/v1/currencies/{id}")
async def del_currency(id: int, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(Currency, id)
    if not item:
        raise HTTPException(404, "Валюта не найдена")
    await db.delete(item)
    await db.commit()
    return {"ok": True}


async def crud_list(model, db):
    return (await db.execute(select(model))).scalars().all()


@app.get("/api/v1/stores", response_model=list[StoreOut])
async def stores(db=Depends(get_db)):
    return await crud_list(Store, db)


@app.post("/api/v1/stores", response_model=StoreOut)
async def add_store(data: StoreIn, db=Depends(get_db), _=Depends(protected)):
    item = Store(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@app.patch("/api/v1/stores/{id}", response_model=StoreOut)
async def edit_store(id: int, data: StoreIn, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(Store, id)
    if not item:
        raise HTTPException(404, "Магазин не найден")
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


@app.delete("/api/v1/stores/{id}")
async def del_store(id: int, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(Store, id)
    if not item:
        raise HTTPException(404, "Магазин не найден")
    await db.delete(item)
    await db.commit()
    return {"ok": True}


@app.get("/api/v1/shipping-rates", response_model=list[ShippingOut])
async def shipping(db=Depends(get_db)):
    return await crud_list(ShippingRate, db)


@app.post("/api/v1/shipping-rates", response_model=ShippingOut)
async def add_shipping(data: ShippingIn, db=Depends(get_db), _=Depends(protected)):
    item = ShippingRate(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@app.patch("/api/v1/shipping-rates/{id}", response_model=ShippingOut)
async def edit_shipping(id: int, data: ShippingIn, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(ShippingRate, id)
    if not item:
        raise HTTPException(404, "Тариф не найден")
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


@app.delete("/api/v1/shipping-rates/{id}")
async def del_shipping(id: int, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(ShippingRate, id)
    if not item:
        raise HTTPException(404, "Тариф не найден")
    await db.delete(item)
    await db.commit()
    return {"ok": True}


@app.post("/api/v1/calculator/quote", response_model=QuoteOut)
async def calculate(data: QuoteIn, db=Depends(get_db)):
    try:
        return await quote(db, data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/v1/orders", response_model=OrderOut)
async def create_order(data: OrderIn, db=Depends(get_db)):
    result = await quote(db, data)
    payload = data.model_dump(exclude={"category"})
    item = OrderRequest(
        public_number=f"BF-{secrets.token_hex(4).upper()}",
        **payload,
        used_rate=result["rate"],
        **{k: result[k] for k in ["product_rub", "shipping", "extra_costs", "total", "shipping_pending"]},
    )
    db.add(item)
    db.add(AuditLog(action="create", entity="order", entity_id=item.public_number, details="client order"))
    await db.commit()
    await db.refresh(item)
    return item


@app.get("/api/v1/orders", response_model=list[OrderOut])
async def orders(status: str | None = Query(None), db=Depends(get_db), _=Depends(protected)):
    q = select(OrderRequest).order_by(OrderRequest.created_at.desc())
    if status:
        q = q.where(OrderRequest.status == status)
    return (await db.execute(q)).scalars().all()


@app.get("/api/v1/orders/export.csv")
async def export_early(db=Depends(get_db), _=Depends(protected)):
    items = (await db.execute(select(OrderRequest).order_by(OrderRequest.created_at.desc()))).scalars().all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Номер", "Клиент", "Товар", "Статус", "Итог", "Создана"])
    for item in items:
        writer.writerow([item.public_number, item.client_name, item.product_name, item.status, item.total, item.created_at.isoformat()])
    return StreamingResponse(
        iter([out.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=buyerflow-orders.csv"},
    )


@app.get("/api/v1/orders/{id}", response_model=OrderOut)
async def order(id: int, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(OrderRequest, id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    return item


@app.patch("/api/v1/orders/{id}", response_model=OrderOut)
async def patch_order(id: int, data: OrderPatch, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(OrderRequest, id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    if data.status and data.status not in STATUSES:
        raise HTTPException(422, "Неизвестный статус")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.add(AuditLog(action="update", entity="order", entity_id=str(id), details=str(data.model_dump(exclude_unset=True))))
    await db.commit()
    await db.refresh(item)
    return item


@app.post("/api/v1/orders/{id}/recalculate", response_model=OrderOut)
async def recalc(id: int, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(OrderRequest, id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    data = QuoteIn(
        country=item.country,
        product_url=item.product_url,
        product_name=item.product_name,
        price=item.price,
        currency=item.currency,
        quantity=item.quantity,
        weight=item.weight,
    )
    result = await quote(db, data)
    for k in ["rate", "product_rub", "shipping", "extra_costs", "total", "shipping_pending"]:
        setattr(item, "used_rate" if k == "rate" else k, result[k])
    item.status = "calculated"
    await db.commit()
    await db.refresh(item)
    return item


@app.post("/api/v1/orders/{id}/notify")
async def notify(id: int, db=Depends(get_db), _=Depends(protected)):
    item = await db.get(OrderRequest, id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    await TelegramNotificationService().notify_admin(f"Заявка {item.public_number}: {item.product_name}")
    return {"ok": True}


@app.get("/api/v1/orders/export.csv")
async def export(db=Depends(get_db), _=Depends(protected)):
    items = (await db.execute(select(OrderRequest).order_by(OrderRequest.created_at.desc()))).scalars().all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Номер", "Клиент", "Товар", "Статус", "Итог", "Создана"])
    for x in items:
        writer.writerow([x.public_number, x.client_name, x.product_name, x.status, x.total, x.created_at.isoformat()])
    return StreamingResponse(
        iter([out.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=buyerflow-orders.csv"},
    )
