package com.example.application;

import com.example.domain.Money;
import java.util.List;

/** Use case: depends inward only, and receives its collaborators as ports. */
public final class PriceOrder {

    private PriceOrder() {
    }

    public static Money totalOf(List<Integer> amounts, SaveTotals sink) {
        Money total = new Money(0);
        for (Integer amount : amounts) {
            total = total.plus(new Money(amount));
        }
        sink.save(total);
        return total;
    }

    /** The port belongs to the use case, not to the database package. */
    public interface SaveTotals {
        void save(Money money);
    }
}
