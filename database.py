import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "host": os.getenv("PG_HOST"),
    "port": int(os.getenv("PG_PORT")),
    "database": os.getenv("PG_DATABASE"),
}

async def get_db_pool():
    return await asyncpg.create_pool(**DB_CONFIG)

class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(**DB_CONFIG)
        await self.create_table()

    async def create_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS giveaways (
                    chat_id BIGINT,
                    message_id BIGINT,
                    link TEXT,
                    channel_title TEXT,
                    giveaway_date TEXT,
                    text TEXT
                )
            ''')

    async def close(self):
        if self.pool:
            await self.pool.close()