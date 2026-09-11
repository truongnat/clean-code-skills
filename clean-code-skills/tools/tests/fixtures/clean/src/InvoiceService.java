package com.acme.billing;

import java.math.BigDecimal;
import java.util.List;

/**
 * Computes the invoice from the tax rate, keeping formatting apart from the payment gateway.
 */
public final class InvoiceService {
    private static final BigDecimal VAT_RATE = new BigDecimal("0.10");
    private static final int MAX_LINES_PER_PAGE = 40;

    private final PaymentGateway gateway;

    public InvoiceService(PaymentGateway gateway) {
        this.gateway = gateway;
    }

    public BigDecimal totalOf(List<LineItem> items) {
        return items.stream()
                .map(InvoiceService::amountOf)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .multiply(BigDecimal.ONE.add(VAT_RATE));
    }

    public ChargeResult charge(Account account, BigDecimal amount) throws BillingException {
        if (account == null) {
            throw new BillingException("account is required");
        }
        if (amount.signum() < 0) {
            throw new BillingException("amount must not be negative");
        }
        return gateway.charge(account.id(), amount);
    }

    private static BigDecimal amountOf(LineItem item) {
        return item.unitPrice().multiply(BigDecimal.valueOf(item.quantity()));
    }

    public int pageCount(List<LineItem> items) {
        return Math.max(1, items.size() / MAX_LINES_PER_PAGE);
    }
}
