"""Adapter: this is where the driver belongs."""
from __future__ import annotations

from sqlalchemy import create_engine

from app.application.ports import OrderRepository
from app.domain.money import Money


def order_table() -> str:
    return "orders"


class SqlOrderRepository(OrderRepository):
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url)

    def save_total(self, money: Money) -> None:
        print("would persist", money.amount)
