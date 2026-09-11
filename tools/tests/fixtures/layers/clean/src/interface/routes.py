"""Composition root stays outermost."""
from ..application.orders import price_order
from ..infrastructure.db import SqlOrderRepository


def handle(items: list) -> dict:
    return {"total": price_order(SqlOrderRepository("sqlite://"), items).amount}
