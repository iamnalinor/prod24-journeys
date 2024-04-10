from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "journey" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL
);
        CREATE TABLE IF NOT EXISTS "journeylocation" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "area_id" INT NOT NULL,
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL
);
        CREATE TABLE IF NOT EXISTS "journeynote" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "author_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
        CREATE TABLE "journey_user" (
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "journey_id" BIGINT NOT NULL REFERENCES "journey" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "journey_user";
        DROP TABLE IF EXISTS "journey";
        DROP TABLE IF EXISTS "journeylocation";
        DROP TABLE IF EXISTS "journeynote";"""
