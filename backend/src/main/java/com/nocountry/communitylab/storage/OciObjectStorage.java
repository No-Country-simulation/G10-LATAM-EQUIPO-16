package com.nocountry.communitylab.storage;

public interface OciObjectStorage {
    void putObject(String bucket, String objectRoute, byte[] content);
}