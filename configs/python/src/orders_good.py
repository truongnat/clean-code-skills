"""Order pricing: computation kept apart from I/O so tests need no database.

The compliant version shipped with the `clean-code` skill. With the config in this folder:

    ruff check src/orders_good.py
    black --check src/orders_good.py
    mypy src/orders_good.py

all three stay silent. Want to see the difference? Compare `orders_bad.py` in the same folder.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

CENT = Decimal("0.01")
ZERO = Decimal(0)
FREE_SHIPPING_THRESHOLD = Decimal("500000")
FLAT_SHIPPING_FEE = Decimal("30000")
VAT_RATE = Decimal("0.10")


@dataclass(frozen=True)
class LineItem:
    """A cart line - it knows whether it can be sold."""

    price: Decimal
    quantity: int
    stock: int
    blocked: bool = False

    def is_sellable(self) -> bool:
        """Sellable when in stock, not locked and priced above zero."""
        return not self.blocked and self.stock > 0 and self.price > ZERO

    def amount(self) -> Decimal:
        """Line total for this cart line."""
        return item_total(self)


@dataclass(frozen=True)
class Cart:
    """Immutable cart."""

    items: tuple[LineItem, ...]

    def sellable_items(self) -> tuple[LineItem, ...]:
        """Only valid lines enter the pricing."""
        return tuple(item for item in self.items if item.is_sellable())


def item_total(item: LineItem) -> Decimal:
    """Unit price times quantity."""
    return item.price * item.quantity


def subtotal_of(cart: Cart) -> Decimal:
    """Merchandise subtotal. Reads only, changes nothing (a query)."""
    return sum((item_total(item) for item in cart.sellable_items()), ZERO)


def round_to_cent(amount: Decimal) -> Decimal:
    """Round to the currency minor unit."""
    return amount.quantize(CENT)


def vat_of(amount: Decimal) -> Decimal:
    """VAT computed on the merchandise total."""
    return round_to_cent(amount * VAT_RATE)


def shipping_for(subtotal: Decimal) -> Decimal:
    """Free shipping above the threshold, otherwise a flat fee."""
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return ZERO
    return FLAT_SHIPPING_FEE


def total_for(cart: Cart) -> Decimal:
    """Grand total = merchandise + VAT + shipping."""
    merchandise = subtotal_of(cart)
    return round_to_cent(merchandise + vat_of(merchandise) + shipping_for(merchandise))
