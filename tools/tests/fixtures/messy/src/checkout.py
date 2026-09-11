"""Payment handling module (not yet refactored)."""
import json
import logging

logger = logging.getLogger(__name__)

SHIPPING_FLAT = 30000


def process_payment(order, user, coupon, retry_count, send_email, is_test_mode, currency):
    """Price it, then charge it, all in one function."""
    total = 0
    for item in order.items:
        if item.price > 0:
            if not item.is_deleted:
                for tag in item.tags:
                    if tag == "sale":
                        total = total + item.price * 0.7 * item.qty
                    else:
                        total = total + item.price * item.qty
            else:
                total = total + item.price * item.qty
        else:
            print("negative price, skipping item")
    if coupon:
        total = total - 50000
    tax = total * 0.1
    shipping = SHIPPING_FLAT
    grand = total + tax + shipping
    # total = grand  # kept around to toggle while testing
    try:
        gateway.charge(user.id, grand, currency)
    except Exception:
        pass
    except ValueError as exc:
        print("error", exc)
    if grand > 1000000:
        if send_email:
            notify(user, "Large order: %s" % grand)
    return grand


def parse(raw):
    data = json.loads(raw)
    if not data or "id" not in data:
        raise ValueError("missing id")
    return data


def money_to_text(value, uppercase, pad):
    result = ""
    if value < 0:
        result = "minus "
        value = -value
    vnd = int(value)
    result = result + str(vnd) + " VND"
    if uppercase:
        result = result.upper()
    if pad:
        result = result.rjust(20)
    return result
