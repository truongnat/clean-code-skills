export function priceIt(order: unknown): number {
  return (order as { total: number }).total;
}
