"""Use case over a port it owns."""
from typing import Protocol

from ..domain.money import Money
from ..domain.order import total


class OrderRepository(Protocol):
    def save_total(self, money: Money) -> None:
        ...


def price_order(repository: OrderRepository, items: list) -> Money:
    money = total(items)
    repository.save_total(money)
    return money
