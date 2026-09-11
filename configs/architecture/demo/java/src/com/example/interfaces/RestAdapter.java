package com.example.interfaces;

import com.example.application.PriceOrder;
import com.example.infrastructure.OrderRepository;
import java.util.List;

/** Composition root stays at the outermost ring: it may know everyone. */
public final class RestAdapter {

    public int handle(List<Integer> amounts) {
        return PriceOrder.totalOf(amounts, new OrderRepository()).amount();
    }
}
