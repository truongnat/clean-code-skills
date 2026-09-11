"""Use case that reaches for the ORM directly."""
from sqlalchemy import select  # driver in the application layer
from ..domain.order import total  # inward, fine


def create_order(repo, order) -> int:
    return total(order).amount
