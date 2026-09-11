"""DEMO OF A BROKEN LAYERING - two violations on purpose."""
from __future__ import annotations

import sqlalchemy  # forbidden: the domain may not know the ORM
from app.infrastructure.db import order_table  # forbidden: inner imports outer


def legacy_total(rows) -> int:
    table = order_table()
    return sum(int(row["amount"]) for row in sqlalchemy.inspect(table).get_columns())
