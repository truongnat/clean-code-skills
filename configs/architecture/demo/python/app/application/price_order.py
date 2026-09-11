"""Use case: depends inward only, and talks to the world through its own port."""
from __future__ import annotations

from app.application.ports import OrderRepository
from app.domain.money import Money


def price_order(items: list[int], repository: OrderRepository) -> Money:
    total = Money(0)
    for amount in items:
        total = total.plus(Money(amount))
    repository.save_total(total)
    return total
