// cc-scan:allow-file LONG_FUNCTION
// Ly do (bat buoc khi xin ngoai le): fixture nay ton tai chi de chung minh co che
// xin-ngoai-le co kiem soat cua cc-scan: khai bao dau file, neu ro ly do.

import { Order } from "./order";

export function veryLongFunction(order: Order): number {
  let sum = 0;
  sum = sum + step0(order.items);
  sum = sum + step1(order.items);
  sum = sum + step2(order.items);
  sum = sum + step3(order.items);
  sum = sum + step4(order.items);
  sum = sum + step5(order.items);
  sum = sum + step6(order.items);
  sum = sum + step7(order.items);
  sum = sum + step8(order.items);
  sum = sum + step9(order.items);
  sum = sum + step10(order.items);
  sum = sum + step11(order.items);
  sum = sum + step12(order.items);
  sum = sum + step13(order.items);
  sum = sum + step14(order.items);
  sum = sum + step15(order.items);
  sum = sum + step16(order.items);
  sum = sum + step17(order.items);
  sum = sum + step18(order.items);
  sum = sum + step19(order.items);
  sum = sum + step20(order.items);
  sum = sum + step21(order.items);
  sum = sum + step22(order.items);
  sum = sum + step23(order.items);
  sum = sum + step24(order.items);
  sum = sum + step25(order.items);
  sum = sum + step26(order.items);
  sum = sum + step27(order.items);
  sum = sum + step28(order.items);
  sum = sum + step29(order.items);
  sum = sum + step30(order.items);
  sum = sum + step31(order.items);
  sum = sum + step32(order.items);
  sum = sum + step33(order.items);
  sum = sum + step34(order.items);
  sum = sum + step35(order.items);
  sum = sum + step36(order.items);
  sum = sum + step37(order.items);
  sum = sum + step38(order.items);
  sum = sum + step39(order.items);
  return sum;
}

export function mixed(value: number): number {
  const notAllowed = value * 9;
  const allowedInline = value * 7; // cc-scan:allow MAGIC_NUMBER - exception on the violating line itself
  // cc-scan:allow MAGIC_NUMBER - exception for the line right below
  const allowedPrev = value * 11;
  console.log(allowedInline, allowedPrev, notAllowed);
  return allowedInline + allowedPrev + notAllowed;
}

function step(n: number): number { return n; }
