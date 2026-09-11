import { Repository } from "./repository";
import { User } from "./user";

// TODO: parked here, refactor later
// const oldTotal = subtotal * 1.21;
// console.log("debug legacy");

const VAT_RATE = 0.1;
const MAX_INLINE_ITEMS = 5;

export class OrderService {
  constructor(private repo: Repository, private mailer: Mailer, private audit: AuditLog, private taxApi: TaxApi) {}

  // handle the order
  public async placeOrder(user: User, items: Item[], coupon: string, force: boolean, skipStockCheck: boolean): Promise<string> {
    let total = 0;
    let message = "";
    if (user) {
      if (items && items.length > 0) {
        for (let i = 0; i < items.length; i++) {
          const it = items[i];
          if (it.price > 0) {
            if (!it.isBlocked && it.stock > 0) {
              total = total + it.price * it.qty;
              if (coupon && coupon.length > 3) {
                if (coupon.startsWith("VIP")) {
                  total = total * 0.8;
                  it.note = "vip coupon applied here with a very long trailing text to force a long line in code";
                } else if (coupon.startsWith("SAVE")) {
                  total = total - 50000;
                } else {
                  total = total - 10000;
                }
              }
            } else {
              console.log("skipping item", it.id);
            }
          } else {
            console.warn("price <= 0");
          }
        }
        total = total + total * VAT_RATE;
        if (total > 500000) {
          message = "needs review";
        }
        if (user.email != null && user.email.includes("@")) {
          try {
            await this.repo.save(user.id, total, message);
          } catch (e) {
          }
        } else {
          try {
            await this.repo.saveLegacy(user, total);
          } catch (err) {
            // TODO: log it here
          }
        }
        if (force) {
          await this.mailer.send(user.email, "Order " + user.id, message);
        }
      } else {
        throw new Error("empty cart");
      }
    }
    return message;
  }

  private buildInvoice(order: Order): string {
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
}
