package com.example.infrastructure;

import com.example.application.PriceOrder;
import com.example.domain.Money;

/** Adapter implements a port the application owns - dependency points inward. */
public final class OrderRepository implements PriceOrder.SaveTotals {

    @Override
    public void save(Money money) {
        System.out.println("persist " + money.amount());
    }

    public String find(String id) {
        return "order:" + id;
    }
}
