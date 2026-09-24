package com.nocountry.communitylab;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import javax.sql.DataSource;
import java.sql.Connection;

@SpringBootTest
@ActiveProfiles("oracle")
public class OciDatabaseTest {

    private final DataSource dataSource;

    @Autowired
    public OciDatabaseTest(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Test
    public void testConexionOracleDatabase() {
        Assertions.assertDoesNotThrow(() -> {
            try (Connection connection = dataSource.getConnection()) {
                String dbProduct = connection.getMetaData().getDatabaseProductName();
                String dbVersion = connection.getMetaData().getDatabaseProductVersion();
                String dbUser = connection.getMetaData().getUserName();

                System.out.println("CONEXIÓN EXITOSA CON EL USUARIO: " + dbUser);
                
                System.out.println("Motor: " + dbProduct + " | Versión: " + dbVersion);


                Assertions.assertNotNull(dbProduct, "El nombre del producto no debe ser nulo.");
            }
        });
    }
}
