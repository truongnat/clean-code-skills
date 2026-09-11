package com.example.domain;

import org.springframework.stereotype.Component; // framework inside the domain
import com.example.infrastructure.OrderRepository;

@Component
public class Order {
    private final OrderRepository repo;

    public Order(OrderRepository repo) {
        this.repo = repo;
    }
}
