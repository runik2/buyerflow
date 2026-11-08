from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def now():
    return datetime.now(timezone.utc)


class Currency(Base):
    __tablename__ = "currencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    base_rate: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=0)
    markup_percent: Mapped[Decimal] = mapped_column(Numeric(7, 3), default=0)
    manual_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80))
    url: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    logo: Mapped[str] = mapped_column(String(20), default="🛍️")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ShippingRate(Base):
    __tablename__ = "shipping_rates"
    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[str] = mapped_column(String(80))
    method: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(80), default="Другое")
    min_weight: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    max_weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    fixed_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    delivery_time: Mapped[str] = mapped_column(String(80), default="Уточняется")
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class OrderRequest(Base):
    __tablename__ = "order_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    client_name: Mapped[str] = mapped_column(String(120))
    telegram_username: Mapped[str] = mapped_column(String(80), default="")
    contact: Mapped[str] = mapped_column(String(160), default="")
    country: Mapped[str] = mapped_column(String(80))
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    product_url: Mapped[str] = mapped_column(String(500))
    product_name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8))
    size: Mapped[str] = mapped_column(String(50), default="")
    color: Mapped[str] = mapped_column(String(80), default="")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    delivery_city: Mapped[str] = mapped_column(String(120))
    used_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    product_rub: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    extra_costs: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    shipping_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    admin_comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(120))
    entity: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
