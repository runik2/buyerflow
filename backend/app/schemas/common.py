from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from urllib.parse import urlparse
import ipaddress
import socket


def safe_url(value: str) -> str:
    if len(value) > 500:
        raise ValueError("URL слишком длинный")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Нужен HTTP(S) URL")
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Внутренний адрес запрещён")
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            ips = [ipaddress.ip_address(x[4][0]) for x in socket.getaddrinfo(host, None)]
        except socket.gaierror:
            ips = []
    if any(ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved for ip in ips):
        raise ValueError("Внутренний адрес запрещён")
    return value


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    username: str
    role: str = "admin"


class CurrencyIn(BaseModel):
    code: str = Field(min_length=2, max_length=8)
    name: str = Field(min_length=1, max_length=80)
    base_rate: Decimal = Field(gt=0)
    markup_percent: Decimal = Field(ge=0, le=500)
    manual_rate: Decimal | None = Field(default=None, gt=0)
    active: bool = True
    valid_until: datetime | None = None


class CurrencyOut(CurrencyIn, ORM):
    id: int
    updated_at: datetime


class StoreIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    country: str = Field(max_length=80)
    category: str = Field(max_length=80)
    url: str
    description: str = Field(default="", max_length=2000)
    logo: str = "🛍️"
    active: bool = True
    sort_priority: int = 0
    _url = field_validator("url")(safe_url)


class StoreOut(StoreIn, ORM):
    id: int
    created_at: datetime


class ShippingIn(BaseModel):
    country: str
    method: str
    category: str = "Другое"
    min_weight: Decimal = Field(default=0, ge=0)
    max_weight: Decimal | None = Field(default=None, gt=0)
    price_per_kg: Decimal = Field(default=0, ge=0)
    fixed_price: Decimal = Field(default=0, ge=0)
    delivery_time: str = "Уточняется"
    currency: str = "RUB"
    active: bool = True


class ShippingOut(ShippingIn, ORM):
    id: int


class QuoteIn(BaseModel):
    country: str
    product_url: str
    product_name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(gt=0)
    currency: str
    quantity: int = Field(default=1, ge=1, le=1000)
    weight: Decimal | None = Field(default=None, gt=0)
    category: str = "Другое"
    _url = field_validator("product_url")(safe_url)


class QuoteOut(BaseModel):
    price: Decimal
    currency: str
    rate: Decimal
    product_rub: Decimal
    shipping: Decimal | None
    extra_costs: Decimal
    total: Decimal | None
    shipping_pending: bool
    message: str = ""


class OrderIn(QuoteIn):
    client_name: str = Field(min_length=1, max_length=120)
    telegram_username: str = Field(default="", max_length=80)
    contact: str = Field(default="", max_length=160)
    store_id: int | None = None
    size: str = ""
    color: str = ""
    delivery_city: str = Field(min_length=1, max_length=120)
    comment: str = Field(default="", max_length=4000)


class OrderPatch(BaseModel):
    status: str | None = None
    admin_comment: str | None = Field(default=None, max_length=4000)


class OrderOut(ORM):
    id: int
    public_number: str
    client_name: str
    telegram_username: str
    contact: str
    country: str
    store_id: int | None
    product_url: str
    product_name: str
    price: Decimal
    currency: str
    size: str
    color: str
    quantity: int
    weight: Decimal | None
    delivery_city: str
    used_rate: Decimal | None
    product_rub: Decimal | None
    shipping: Decimal | None
    extra_costs: Decimal
    total: Decimal | None
    shipping_pending: bool
    comment: str
    status: str
    admin_comment: str
    created_at: datetime
    updated_at: datetime
