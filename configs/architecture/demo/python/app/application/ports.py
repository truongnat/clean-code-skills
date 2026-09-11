"""The use case owns the abstraction it needs."""
from __future__ import annotations

from typing import Protocol

from app.domain.money import Money


class OrderRepository(Protocol):
    def save_total(self, money: Money) -> None: ...
