import { priceIt } from '../pricing/index';

export function place(order: unknown): number {
  return priceIt(order);
}
