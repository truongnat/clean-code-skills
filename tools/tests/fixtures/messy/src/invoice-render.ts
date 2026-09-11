import { Order } from "./order";

export function renderInvoice(order: Order): string {
  const lines: string[] = [];
  lines.push("INVOICE");
  lines.push("id: " + order.id);
  lines.push("total: " + order.total);
  lines.push("tax: " + order.tax);
  lines.push("date: " + order.date);
  lines.push("customer: " + order.customer);
  lines.push("phone: " + order.phone);
  lines.push("address: " + order.address);
  return lines.join("\n");
}
