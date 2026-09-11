/**
 * Behaviour tests for `priceCart` - they run in 0ms because pricing is pure (no DB mock).
 * This is the safety net for every refactoring above.
 */
import { describe, expect, it } from "vitest";
import { priceCart, type CartLine, type PlaceOrderCommand } from "./order-service";

const line = (over: Partial<CartLine> = {}): CartLine => ({
  id: "sku-1", priceVnd: 100_000, quantity: 1, stock: 5, blocked: false, ...over,
});

const command = (over: Partial<PlaceOrderCommand> = {}): PlaceOrderCommand => ({
  userId: "u1",
  customerEmail: "a@b.c",
  items: [line()],
  currency: "VND",
  notify: "onForce",
  stockPolicy: "enforce",
  ...over,
});

describe("priceCart", () => {
  it("rejects a cart whose every line is blocked, and creates no order", () => {
    expect(priceCart(command({ items: [line({ blocked: true })] }))).toEqual({
      ok: false, totalVnd: 0, status: "rejected",
    });
  });

  it("a VIP coupon takes 20% off", () => {
    const quote = priceCart(command({ coupon: "VIP-2026" }));
    expect(quote.totalVnd).toBe(80_000);
  });

  it("a standard coupon subtracts a fixed amount", () => {
    expect(priceCart(command({ coupon: "SAVE10" })).totalVnd).toBe(75_000);
  });

  it("short stock means backorder; stockPolicy=skip skips the check", () => {
    const outOfStock = command({ items: [line({ quantity: 9 })] });
    expect(priceCart(outOfStock).status).toBe("backorder");
    expect(priceCart({ ...outOfStock, stockPolicy: "skip" }).status).toBe("new");
  });

  it("an order of 500k or more needs review", () => {
    const big = command({ items: [line({ priceVnd: 600_000 })] });
    expect(priceCart(big).status).toBe("needs_review");
  });
});
