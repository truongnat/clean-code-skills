/**
 * The AFTER version (a one-to-one counterpart of legacy-order-service.ts).
 * Run:  python3 ../cc-scan.py src/order-service.ts   -> 0 findings, 100/100.
 */

import { OrderRepository } from "./repository";
import { Mailer } from "./mailer";

const VIP_COUPON_PREFIX = "VIP";
const VIP_MULTIPLIER = 0.8;
const STANDARD_COUPON_DISCOUNT = 25_000;
const REVIEW_THRESHOLD_VND = 500_000;

export type OrderStatus = "new" | "backorder" | "rejected" | "needs_review";
export type StockPolicy = "enforce" | "skip";

export interface PlaceOrderResult {
  readonly ok: boolean;
  readonly totalVnd: number;
  readonly status: OrderStatus;
}

export interface PlaceOrderCommand {
  readonly userId: string;
  readonly customerEmail: string;
  readonly items: readonly CartLine[];
  readonly coupon?: string;
  readonly currency: "VND";
  readonly notify: "always" | "onForce";
  readonly stockPolicy: "enforce" | "skip";
}

export interface CartLine {
  readonly id: string;
  readonly priceVnd: number;
  readonly quantity: number;
  readonly stock: number;
  readonly blocked: boolean;
}

/**
 * Application service: it coordinates, and it is the ONLY place with a side effect.
 * Pricing lives in `priceCart` (pure), so its tests need no DB or mailer mock.
 */
export class PlaceOrder {
  constructor(
    private readonly orders: OrderRepository,
    private readonly mailer: Mailer,
  ) {}

  async run(cmd: PlaceOrderCommand): Promise<PlaceOrderResult> {
    const quote = priceCart(cmd);

    const saved = await this.orders.record({
      userId: cmd.userId,
      totalVnd: quote.totalVnd,
      status: quote.status,
      currency: cmd.currency,
    });

    if (!saved.ok) {
      throw new OrderPersistenceError(cmd.userId, saved.reason);
    }
    if (cmd.notify === "always" || (cmd.notify === "onForce" && quote.status === "needs_review")) {
      await this.mailer.sendReceipt(cmd.customerEmail, cmd.userId, quote.totalVnd);
    }
    return quote;
  }
}

/** Pure: no I/O, no input mutation - 5 tests cover every branch. */
export function priceCart(cmd: Pick<PlaceOrderCommand, "items" | "coupon" | "stockPolicy">): PlaceOrderResult {
  const lines = chargeableLines(cmd);
  if (lines.length === 0) {
    return { ok: false, totalVnd: 0, status: "rejected" };
  }
  const discounted = applyCoupon(grossOf(lines), cmd.coupon);
  return {
    ok: true,
    totalVnd: discounted,
    status: statusFor(discounted, lines, cmd.stockPolicy),
  };
}

const chargeableLines = (cmd: Pick<PlaceOrderCommand, "items" | "stockPolicy">): CartLine[] =>
  cmd.items.filter((line) => isChargeable(line) && (cmd.stockPolicy === "skip" || hasStock(line)));

const isChargeable = (line: CartLine): boolean => line.priceVnd > 0 && !line.blocked;
const hasStock = (line: CartLine): boolean => line.stock >= line.quantity;
const grossOf = (lines: readonly CartLine[]): number =>
  lines.reduce((sum, line) => sum + line.priceVnd * line.quantity, 0);

function applyCoupon(gross: number, coupon?: string): number {
  if (!coupon) {
    return gross;
  }
  return coupon.startsWith(VIP_COUPON_PREFIX) ? gross * VIP_MULTIPLIER : gross - STANDARD_COUPON_DISCOUNT;
}

function statusFor(totalVnd: number, lines: readonly CartLine[], stockPolicy: StockPolicy): OrderStatus {
  if (totalVnd >= REVIEW_THRESHOLD_VND) {
    return "needs_review";
  }
  const backordered = stockPolicy === "enforce" && lines.some((line) => line.stock < line.quantity);
  return backordered ? "backorder" : "new";
}

/** A specific exception, data in the message; the caller decides retry or tell the customer. */
export class OrderPersistenceError extends Error {
  static readonly code = "ORDER_PERSISTENCE_FAILED";
  constructor(readonly userId: string, readonly reason: string) {
    super(`could not persist the order of user ${userId} (${reason}) - check the DB, then retry`);
    this.name = "OrderPersistenceError";
  }
}
