package com.acme.billing;

/**
 * Order totals. One job per function, no mutation of the inputs,
 * no magic numbers, no I/O, so plain JUnit is enough to test it.
 */
public final class OrderTotalsGood {
    private static final double VIP_MULTIPLIER = 0.9;
    private static final double STANDARD_MULTIPLIER = 1.0;
    private static final int COUPON_MIN_LENGTH = 3;

    private OrderTotalsGood() {
    }

    /** Sum over valid lines; negative prices and over-cap lines are skipped. */
    public static double subtotal(final double[] prices, final int[] quantities, final int limit) {
        double sum = 0.0;
        int considered = Math.min(prices.length, limit);
        for (int index = 0; index < considered; index++) {
            if (isChargeable(prices[index], quantities[index])) {
                sum += prices[index] * quantities[index];
            }
        }
        return sum;
    }

    private static boolean isChargeable(final double price, final int quantity) {
        return price > 0.0 && quantity > 0;
    }

    /** Applies a VIP coupon; coupons shorter than COUPON_MIN_LENGTH are ignored. */
    public static double withVipDiscount(final double subtotal, final String coupon) {
        if (coupon == null || coupon.length() < COUPON_MIN_LENGTH) {
            return subtotal;
        }
        return subtotal * VIP_MULTIPLIER;
    }

    /** Currency multiplier per money unit; 1.0 when the rate is unknown. */
    public static double inCurrency(final double amount, final double unitRate) {
        if (unitRate <= 0.0) {
            return amount * STANDARD_MULTIPLIER;
        }
        return amount * unitRate;
    }
}
