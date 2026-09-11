package com.example.domain;

import java.util.Objects;

/** Business rule, expressed in plain Java: no JDBC, no framework, no outer layer. */
public final class Money {

    private final int amount;

    public Money(int amount) {
        this.amount = amount;
    }

    public int amount() {
        return amount;
    }

    public Money plus(Money other) {
        return new Money(amount + other.amount);
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof Money && ((Money) obj).amount == amount;
    }

    @Override
    public int hashCode() {
        return Objects.hash(amount);
    }
}
