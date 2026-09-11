"""Shipping fees and invoice output (the refactored version)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

FREE_SHIPPING_THRESHOLD = 500_000
FLAT_SHIPPING_FEE = 30_000
HEAVY_SURCHARGE_PER_KG = 2_000
HEAVY_THRESHOLD_KG = 20


@dataclass(frozen=True)
class Parcel:
    weight_kg: int
    subtotal: int


def shipping_fee(parcel: Parcel) -> int:
    """Shipping = flat fee + heavy-item surcharge, free at or above the threshold."""
    if parcel.subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    return FLAT_SHIPPING_FEE + heavy_surcharge(parcel.weight_kg)


def heavy_surcharge(weight_kg: int) -> int:
    if weight_kg <= HEAVY_THRESHOLD_KG:
        return 0
    return (weight_kg - HEAVY_THRESHOLD_KG) * HEAVY_SURCHARGE_PER_KG


def total_for(parcel: Parcel) -> int:
    total = parcel.subtotal + shipping_fee(parcel)
    logger.debug("pricing done: %s", total)
    return total


def describe(parcel: Parcel) -> str:
    parts = [f"subtotal={parcel.subtotal}", f"ship={shipping_fee(parcel)}"]
    return ", ".join(parts)
