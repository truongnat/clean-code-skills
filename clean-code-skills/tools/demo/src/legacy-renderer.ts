// The demo's second file: it holds the 8-line block duplicated from buildInvoice in legacy-order-service.ts.

export function renderInvoice(order: any): string {
  const lines: string[] = [];
  lines.push("INVOICE");
  lines.push("id: " + order.id);
  lines.push("total: " + order.total);
  lines.push("tax: " + order.tax);
  lines.push("date: " + order.date);
  lines.push("customer: " + order.customer);
  return lines.join("\n");
}
