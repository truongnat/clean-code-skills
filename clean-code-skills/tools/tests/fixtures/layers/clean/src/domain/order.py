"""Pure domain: no framework, no outer import."""
from .money import Money


def total(items: list) -> Money:
    return Money(sum(item.amount for item in items))
