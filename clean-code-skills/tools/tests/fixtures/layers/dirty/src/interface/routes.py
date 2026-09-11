"""HTTP layer wiring."""
from ..application.orders import create_order  # inward, fine


def build_response(payload: dict) -> dict:
    return {"ok": True, "payload": payload}
