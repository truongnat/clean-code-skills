export function processOrder(order: any, retry: number, coupon: string, force: boolean, notify: boolean, cur: string): string {
  let total = 0;
  for (const it of order.items) {
    if (it.price > 0) {
      if (!it.blocked) {
        total += it.price * it.qty;
      }
    }
  }
  if (coupon) {
    total = total - 50000;
  }
  console.log("total", total);
  const x = order.status == "paid" ? 1 : 2;
  // total = total * 1.1;
  return `${total}-${x}-${cur}-${retry}-${force}-${notify}-${total}`;
}
