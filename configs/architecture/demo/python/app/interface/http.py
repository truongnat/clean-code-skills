"""Composition root at the outermost ring."""
from __future__ import annotations

from app.application.price_order import price_order
from app.infrastructure.db import SqlOrderRepository


def handle(items: list[int]) -> dict[str, int]:
    repository = SqlOrderRepository("sqlite://")
    return {"total": price_order(items, repository).amount}
