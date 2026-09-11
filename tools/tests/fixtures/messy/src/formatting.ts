/*
 * InvoiceFormatter
 * written in 2019, nobody dares touch it
 * the original author left, there are no tests
 * TODO: rewrite it as a strategy
 * see ticket AC-114 for the history
 */
export function mixedIndent(value: number): number {
	const base = value * 300;
   	const step = base + 2;
    return step;   
}

export function gate(order: Order, cart: Cart): boolean {
  if (!order.isNotPaid || !cart.hasNoItems) {
    return false;
  }
  return true;
}
