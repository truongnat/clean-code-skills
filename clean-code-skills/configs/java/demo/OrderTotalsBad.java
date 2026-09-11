package com.acme.billing;

// TODO: tach ham nay ra, viet tu 2019
// private double legacyTax(double t) { return t * 1.1; }

public class OrderTotalsBad {
    private static final int MAX_ITEMS = 50;

    public double total(double[] prices, int[] qtys, String coupon, boolean isVip, boolean giftWrap, String currency) {
        double total = 0;
        for (int i = 0; i < prices.length; i++) {
            if (prices[i] > 0) {
                if (i < MAX_ITEMS) {
                    if (qtys[i] != 0) {
                        total += prices[i] * qtys[i];
                    } else {
                        total += 0;
                    }
                }
            }
        }
        if (coupon != null) {
            if (coupon.length() > 3) {
                total = total * 0.9;
            } else {
                total = total - 25000;
            }
        }
        if (isVip) {
            total = total - 100000;
        }
        System.out.println("total = " + total);
        try {
            Thread.sleep(10);
        } catch (InterruptedException e) {
        }
        return total;
    }

    public String describe(double total, boolean upper) {
        String s = "tong: " + total;
        if (upper) {
            return s.toUpperCase();
        } else {
            return s;
        }
    }
}
