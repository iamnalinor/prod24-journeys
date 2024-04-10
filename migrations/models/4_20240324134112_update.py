from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "journeylocation" ALTER COLUMN "area_id" TYPE BIGINT USING "area_id"::BIGINT;
        ALTER TABLE "user" ALTER COLUMN "home_area_id" TYPE BIGINT USING "home_area_id"::BIGINT;
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "home_area_id" TYPE INT USING "home_area_id"::INT;
        ALTER TABLE "journeylocation" ALTER COLUMN "area_id" TYPE INT USING "area_id"::INT;"""
