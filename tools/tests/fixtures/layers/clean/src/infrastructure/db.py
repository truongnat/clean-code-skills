"""Adapter implements the port; the driver lives here, where it belongs."""
from sqlalchemy import create_engine

from ..application.orders import OrderRepository


class SqlOrderRepository(OrderRepository):
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url)

    def save_total(self, money) -> None:
        print("saved", money.amount)
