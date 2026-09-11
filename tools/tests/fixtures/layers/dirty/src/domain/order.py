"""Domain that knows about the database."""
import sqlalchemy  # driver in the domain
from ..infrastructure.db import OrdersTable  # outward import
from .money import Money


def total(order) -> Money:
    return Money(sum(item.amount for item in order.items))
