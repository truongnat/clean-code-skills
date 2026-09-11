# Deliberately violating demo so the rules fire. Do not copy this pattern.
import json
import os
from typing import Any

# total = total * 1.1   <- leftover from the old code


def calc(cart, user, cfg, mode, send_email, is_test, dbg):
    total = 0
    for it in cart:
        if it["price"] > 0:
            if not it.get("blocked"):
                if it["qty"] != 0:
                    total += it["price"] * it["qty"]
                    if mode == 1:
                        total = total * 0.9
                    elif mode == 2:
                        total = total * 0.85
                    else:
                        total = total
                else:
                    total += 0
            else:
                total += 0
        else:
            print("bo qua item", it)
    try:
        data = json.loads(open(os.path.join(cfg["dir"], "tax.json")).read())
        total += data["rate"] * total
    except:
        pass
    if send_email:
        if user:
            if user.get("email"):
                print("mail", user["email"], total)
            else:
                raise Exception("user khong co email")
        else:
            raise Exception("missing user")
    return total


def parse(raw: str) -> Any:
    d = json.loads(raw)
    if d == None:
        raise ValueError("empty")
    return d


class Manager:
    def __init__(self, data):
        self.data = data

    def do(self, x):
        return x + 1
