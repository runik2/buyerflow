from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from app.models.entities import Currency, ShippingRate


async def quote(db, data):
    cur = (await db.execute(select(Currency).where(Currency.code == data.currency.upper(), Currency.active.is_(True)))).scalar_one_or_none()
    if not cur:
        raise ValueError("Валюта не найдена или выключена")
    rate = cur.manual_rate or (cur.base_rate * (Decimal(1) + cur.markup_percent / Decimal(100)))
    rate = rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    product_rub = (data.price * data.quantity * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rates = (
        (await db.execute(select(ShippingRate).where(ShippingRate.country == data.country, ShippingRate.active.is_(True)))).scalars().all()
    )
    shipping = None
    for item in rates:
        if data.weight is not None and data.weight >= item.min_weight and (item.max_weight is None or data.weight <= item.max_weight):
            shipping = item.fixed_price + data.weight * item.price_per_kg
            break
        if data.weight is None and item.price_per_kg == 0:
            shipping = item.fixed_price
            break
    pending = shipping is None
    total = None if pending else product_rub + shipping
    return {
        "price": data.price,
        "currency": data.currency.upper(),
        "rate": rate,
        "product_rub": product_rub,
        "shipping": shipping,
        "extra_costs": Decimal(0),
        "total": total,
        "shipping_pending": pending,
        "message": "Расчёт доставки уточняется" if pending else "",
    }
