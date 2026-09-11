import { describe, expect, it } from "vitest";
import { couponDiscount, shippingFor, subtotalOf, vatOf } from "./pricing";

const cart = (prices: number[]) => ({
  currency: "VND",
  items: prices.map((price, i) => ({ price, quantity: 1, stock: 1, blocked: false, id: `i${i}` })),
});

describe("pricing", () => {
  it("skips blocked or out-of-stock items", () => {
    const items = cart([10, 20]);
    items.items[0].blocked = true;
    expect(subtotalOf(items as never)).toBe(20);
  });

  it("ships free above the threshold", () => {
    expect(shippingFor(600_000)).toBe(0);
    expect(shippingFor(100)).toBe(30_000);
  });

  it("applies 10% tax", () => {
    expect(vatOf(1000)).toBe(100);
  });

  it("gives no discount for an invalid coupon", () => {
    expect(couponDiscount("VIP", 5000)).toBe(0);
  });
});
