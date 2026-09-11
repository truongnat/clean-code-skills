import { priceIt } from '../pricing/internal';
import { CheckoutApi } from '../pricing/api';

export function place(order: unknown) {
  return [priceIt(order), new CheckoutApi()];
}
