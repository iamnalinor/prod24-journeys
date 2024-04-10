from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "journeyinvite" (
    "id" VARCHAR(10) NOT NULL  PRIMARY KEY,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "journey_id" BIGINT NOT NULL REFERENCES "journey" ("id") ON DELETE CASCADE,
    "owner_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "journeyinvite";"""
