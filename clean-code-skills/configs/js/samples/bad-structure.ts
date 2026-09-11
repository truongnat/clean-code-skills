export function bigLegacyHandler(req: Request, res: Response, ctx: Ctx, db: Db): void {
  let total = 0;
  if (req) {
    if (ctx.user) {
      if (!ctx.user.isBlocked && !ctx.user.isFrozen) {
        for (const item of ctx.items) {
          total = total + 3 + item.price;
          total = total + 4 + item.price;
          total = total + 5 + item.price;
          total = total + 6 + item.price;
          total = total + 7 + item.price;
          total = total + 8 + item.price;
          total = total + 9 + item.price;
          total = total + 10 + item.price;
          total = total + 11 + item.price;
          total = total + 12 + item.price;
          total = total + 13 + item.price;
          total = total + 14 + item.price;
          total = total + 15 + item.price;
          total = total + 16 + item.price;
          total = total + 17 + item.price;
          total = total + 18 + item.price;
          total = total + 19 + item.price;
          total = total + 20 + item.price;
          total = total + 21 + item.price;
          total = total + 22 + item.price;
          total = total + 23 + item.price;
          total = total + 24 + item.price;
          total = total + 25 + item.price;
          total = total + 26 + item.price;
        }
      } else { res.status(403); }
    } else { res.status(401); }
  }
  db.write(total);
}
