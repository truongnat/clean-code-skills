/**
 * Passes the standard: short functions, few parameters, guard clauses, no magic numbers.
 * `npx eslint samples/good-example.ts` must report 0 problems.
 */
const FREE_SHIPPING_THRESHOLD_VND = 500_000;
const FLAT_SHIPPING_VND = 30_000;

export interface CartLike {
  readonly items: readonly { readonly price: number }[];
}

export function subtotalOf(cart: CartLike): number {
  return cart.items.reduce((sum, item) => sum + item.price, 0);
}

export function shippingFor(subtotal: number): number {
  if (subtotal >= FREE_SHIPPING_THRESHOLD_VND) {
    return 0;
  }
  return subtotal > 0 ? FLAT_SHIPPING_VND : 0;
}

export function totalFor(cart: CartLike): number {
  const subtotal = subtotalOf(cart);
  return subtotal + shippingFor(subtotal);
}
