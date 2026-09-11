import type { Cart, Money } from "./types";
import { Logger } from "./logger";

const VAT_RATE = 0.1;
const FREE_SHIPPING_THRESHOLD = 500_000;
const SHIPPING_FLAT = 30_000;
const VIP_COUPON_PREFIX = "VIP";
const COUPON_MIN_LENGTH = 3;
const VIP_DISCOUNT_RATE = 0.5;
const MAX_SAVE_DISCOUNT = 20_000;
const DECIMAL_BASE = 10;

export interface PricingContext {
  readonly cart: Cart;
  readonly couponCode?: string;
  readonly locale?: string;
}

/** Total before tax - does not change the cart's state. */
export function subtotalOf(cart: Cart): number {
  return cart.items
    .filter((item) => isSellable(item))
    .reduce((sum, item) => sum + lineTotal(item), 0);
}

export function vatOf(amount: number): number {
  return roundTo(amount * VAT_RATE, 0);
}

export function shippingFor(amount: number): number {
  if (amount >= FREE_SHIPPING_THRESHOLD) {
    return 0;
  }
  return SHIPPING_FLAT;
}

export function couponDiscount(coupon: string | undefined, amount: number): number {
  if (!coupon || coupon.length < COUPON_MIN_LENGTH) {
    return 0;
  }
  if (coupon.startsWith(VIP_COUPON_PREFIX)) {
    return amount * VIP_DISCOUNT_RATE;
  }
  return Math.min(amount, MAX_SAVE_DISCOUNT);
}

export function totalFor(ctx: PricingContext): Money {
  const gross = subtotalOf(ctx.cart);
  const discounted = gross - couponDiscount(ctx.couponCode, gross);
  const total = discounted + vatOf(discounted) + shippingFor(discounted);
  Logger.debug("pricing computed", { gross, total });
  return { amount: total, currency: ctx.cart.currency };
}

function isSellable(item: Cart["items"][number]): boolean {
  return item.price > 0 && !item.blocked && item.stock > 0;
}

function lineTotal(item: Cart["items"][number]): number {
  return item.price * item.quantity;
}

function roundTo(value: number, decimals: number): number {
  const factor = DECIMAL_BASE ** decimals;
  return Math.round(value * factor) / factor;
}
