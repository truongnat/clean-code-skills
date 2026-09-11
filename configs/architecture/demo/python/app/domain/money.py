"""Pure domain: no framework types, no outer imports."""
from __future__ import annotations


class Money:
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def plus(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)
