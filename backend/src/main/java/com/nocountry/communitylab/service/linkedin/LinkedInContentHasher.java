package com.nocountry.communitylab.service.linkedin;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

public final class LinkedInContentHasher {

    private LinkedInContentHasher() {
    }

    public static String sha256(String content) {
        if (content == null) {
            throw new IllegalArgumentException("El contenido no puede ser null");
        }

        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(
                content.getBytes(StandardCharsets.UTF_8)
            );

            return HexFormat.of().formatHex(hash);

        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(
                "SHA-256 no está disponible",
                exception
            );
        }
    }

    public static boolean matches(String content, String expectedHash) {
        if (content == null || expectedHash == null) {
            return false;
        }

        String actualHash = sha256(content);

        if (expectedHash.length() != actualHash.length()) {
            return false;
        }

        return MessageDigest.isEqual(
            actualHash.getBytes(StandardCharsets.US_ASCII),
            expectedHash.getBytes(StandardCharsets.US_ASCII)
        );
    }
}
