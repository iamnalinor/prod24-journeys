from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "home_area_id" INT;
        ALTER TABLE "user" ADD "bio" TEXT;
        ALTER TABLE "user" ADD "age" INT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" DROP COLUMN "home_area_id";
        ALTER TABLE "user" DROP COLUMN "bio";
        ALTER TABLE "user" DROP COLUMN "age";"""
