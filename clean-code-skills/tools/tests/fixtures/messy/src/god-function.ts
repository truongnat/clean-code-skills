export async function processCheckout(order: Order, ctx: Ctx): Promise<Result> {
  const r0 = await validate(order, ctx);
  if (r0.failed) { throw new Error(`step validate failed at 0`); }
  const r1 = await normalise(order, ctx);
  if (r1.failed) { throw new Error(`step normalise failed at 1`); }
  const r2 = await roundAmount(order, ctx);
  if (r2.failed) { throw new Error(`step roundAmount failed at 2`); }
  const r3 = await applyVat(order, ctx);
  if (r3.failed) { throw new Error(`step applyVat failed at 3`); }
  const r4 = await applyShipping(order, ctx);
  if (r4.failed) { throw new Error(`step applyShipping failed at 4`); }
  const r5 = await applyDiscount(order, ctx);
  if (r5.failed) { throw new Error(`step applyDiscount failed at 5`); }
  const r6 = await reserveStock(order, ctx);
  if (r6.failed) { throw new Error(`step reserveStock failed at 6`); }
  const r7 = await chargeCard(order, ctx);
  if (r7.failed) { throw new Error(`step chargeCard failed at 7`); }
  const r8 = await sendReceipt(order, ctx);
  if (r8.failed) { throw new Error(`step sendReceipt failed at 8`); }
  const r9 = await syncErp(order, ctx);
  if (r9.failed) { throw new Error(`step syncErp failed at 9`); }
  const r10 = await notifyPartner(order, ctx);
  if (r10.failed) { throw new Error(`step notifyPartner failed at 10`); }
  const r11 = await updateIndex(order, ctx);
  if (r11.failed) { throw new Error(`step updateIndex failed at 11`); }
  const r12 = await flushCache(order, ctx);
  if (r12.failed) { throw new Error(`step flushCache failed at 12`); }
  const r13 = await auditTrail(order, ctx);
  if (r13.failed) { throw new Error(`step auditTrail failed at 13`); }
  const r14 = await closeDraft(order, ctx);
  if (r14.failed) { throw new Error(`step closeDraft failed at 14`); }
  const r15 = await rebuildTotals(order, ctx);
  if (r15.failed) { throw new Error(`step rebuildTotals failed at 15`); }
  const r16 = await checkFraud(order, ctx);
  if (r16.failed) { throw new Error(`step checkFraud failed at 16`); }
  const r17 = await assignDriver(order, ctx);
  if (r17.failed) { throw new Error(`step assignDriver failed at 17`); }
  const r18 = await lockCoupon(order, ctx);
  if (r18.failed) { throw new Error(`step lockCoupon failed at 18`); }
  const r19 = await printLabel(order, ctx);
  if (r19.failed) { throw new Error(`step printLabel failed at 19`); }
  const r20 = await archiveOld(order, ctx);
  if (r20.failed) { throw new Error(`step archiveOld failed at 20`); }
  const r21 = await recalcTax(order, ctx);
  if (r21.failed) { throw new Error(`step recalcTax failed at 21`); }
  const r22 = await mergeDupes(order, ctx);
  if (r22.failed) { throw new Error(`step mergeDupes failed at 22`); }
  const r23 = await pushQueue(order, ctx);
  if (r23.failed) { throw new Error(`step pushQueue failed at 23`); }
  const r24 = await pullResult(order, ctx);
  if (r24.failed) { throw new Error(`step pullResult failed at 24`); }
  const r25 = await reconcile(order, ctx);
  if (r25.failed) { throw new Error(`step reconcile failed at 25`); }
  const r26 = await signDoc(order, ctx);
  if (r26.failed) { throw new Error(`step signDoc failed at 26`); }
  const r27 = await uploadDoc(order, ctx);
  if (r27.failed) { throw new Error(`step uploadDoc failed at 27`); }
  const r28 = await markPaid(order, ctx);
  if (r28.failed) { throw new Error(`step markPaid failed at 28`); }
  const r29 = await clearCart(order, ctx);
  if (r29.failed) { throw new Error(`step clearCart failed at 29`); }
  const r30 = await refreshRates(order, ctx);
  if (r30.failed) { throw new Error(`step refreshRates failed at 30`); }
  const r31 = await computePoints(order, ctx);
  if (r31.failed) { throw new Error(`step computePoints failed at 31`); }
  const r32 = await applyPoints(order, ctx);
  if (r32.failed) { throw new Error(`step applyPoints failed at 32`); }
  const r33 = await emitEvent(order, ctx);
  if (r33.failed) { throw new Error(`step emitEvent failed at 33`); }
  const r34 = await logMetrics(order, ctx);
  if (r34.failed) { throw new Error(`step logMetrics failed at 34`); }
  return { ok: true };
}
