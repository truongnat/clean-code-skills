// Demo file: the "before refactoring" version - deliberately breaks many rules so cc-scan shows it.
// Run:  python3 ../cc-scan.py src/legacy-order-service.ts
// On purpose: a leftover `console.log`, commented-out code, magic numbers, a 60-line function,
// a swallowed catch, boolean flags, deep nesting, duplication, a TODO with no ticket.

import { db } from "./db";
import { Mailer } from "./mailer";

// TODO: refactor this (no ticket -> reported as TODO_MARK)
// const OLD_VAT = 0.05;

export class OrderService {
  constructor(private mailer: Mailer) {}

  public async placeOrder(user: any, items: any[], coupon: string, force: boolean, skipStockCheck: boolean, currency: string): Promise<any> {
    let total = 0;
    let status = "new";
    console.log("placeOrder", user, items, coupon, force);
    if (user) {
      if (items && items.length > 0) {
        for (let i = 0; i < items.length; i++) {
          const it = items[i];
          if (it.price > 0) {
            if (!it.blocked && it.stock > 0) {
              total = total + it.price * it.qty;
              if (coupon) {
                if (coupon.indexOf("VIP") === 0) {
                  total = total * 0.8;
                } else {
                  total = total - 25000;
                }
              }
              if (!skipStockCheck) {
                if (it.stock < it.qty) {
                  status = "backorder";
                }
              }
            } else {
              console.warn("skipping", it.id);
            }
          } else {
            status = "rejected";
          }
        }
        if (total > 500000) {
          status = "needs_review";
        }
        try {
          await db.order.create({ data: { userId: user.id, total, status, currency } });
        } catch (e) {
          // swallowed: the customer is told "order created" while the DB holds nothing
        }
        if (force) {
          try {
            await this.mailer.send(user.email, "Order " + user.id, "total: " + total);
          } catch (e) {
          }
        }
        // total = total * 1.1;   <- the old VAT line, left behind "just in case"
        return { ok: true, total };
      } else {
        throw new Error("empty");
      }
    }
    return { ok: false };
  }

  // the function below DUPLICATES 8 lines of renderInvoice in legacy-renderer.ts -> DUPLICATE_BLOCK
  private buildInvoice(order: any): string {
    const lines: string[] = [];
    lines.push("INVOICE");
    lines.push("id: " + order.id);
    lines.push("total: " + order.total);
    lines.push("tax: " + order.tax);
    lines.push("date: " + order.date);
    lines.push("customer: " + order.customer);
    return lines.join("\n");
  }
}
