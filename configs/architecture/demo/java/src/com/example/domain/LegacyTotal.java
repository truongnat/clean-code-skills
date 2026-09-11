package com.example.domain;

import com.example.infrastructure.OrderRepository;   // violation: inner layer -> outer layer
import java.sql.Connection;                            // violation: a driver type in the domain
import java.sql.SQLException;

/** DELETED BY DESIGN: this is what the architecture tests are supposed to catch. */
public final class LegacyTotal {

    private LegacyTotal() {
    }

    static int of(OrderRepository repository, Connection connection) throws SQLException {
        repository.find("legacy");
        return connection.getAutoCommit() ? 1 : 0;
    }
}
