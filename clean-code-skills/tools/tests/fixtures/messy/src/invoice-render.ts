import { Order } from "./order";

export function renderInvoice(order: Order): string {
  const lines: string[] = [];
  lines.push("HOA DON");
  lines.push("ma: " + order.id);
  lines.push("tong: " + order.total);
  lines.push("thue: " + order.tax);
  lines.push("ngay: " + order.date);
  lines.push("khach: " + order.customer);
  lines.push("dien thoai: " + order.phone);
  lines.push("dia chi: " + order.address);
  return lines.join("\n");
}
