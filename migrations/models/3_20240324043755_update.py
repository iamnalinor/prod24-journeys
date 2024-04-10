from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE "journey_journeylocation" (
    "journey_id" BIGINT NOT NULL REFERENCES "journey" ("id") ON DELETE CASCADE,
    "journeylocation_id" BIGINT NOT NULL REFERENCES "journeylocation" ("id") ON DELETE CASCADE
);
        CREATE TABLE "journey_journeynote" (
    "journeynote_id" BIGINT NOT NULL REFERENCES "journeynote" ("id") ON DELETE CASCADE,
    "journey_id" BIGINT NOT NULL REFERENCES "journey" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "journey_journeynote";
        DROP TABLE IF EXISTS "journey_journeylocation";
        DROP TABLE IF EXISTS "journey_user";"""
