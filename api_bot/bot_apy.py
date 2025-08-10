import os
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from database import Database  # твой класс для работы с PostgreSQL

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

bot_app = Client("bot_session", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

db = Database()  # экземпляр базы


def parse_giveaway_datetime(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None


async def get_today_giveaways():
    today_str = datetime.now().strftime("%Y-%m-%d")
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT Link, ChannelTitle, GiveawayDate
            FROM giveaways
            WHERE GiveawayDate = $1
            """,
            today_str
        )
    return rows


async def get_future_giveaways():
    today_str = datetime.now().strftime("%Y-%m-%d")
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT Link, ChannelTitle, GiveawayDate
            FROM giveaways
            WHERE GiveawayDate >= $1
            ORDER BY GiveawayDate ASC
            """,
            today_str
        )
    return rows


@bot_app.on_message(filters.command("today"))
async def today_handler(client, message):
    giveaways = await get_today_giveaways()
    if not giveaways:
        await message.reply("Сегодня розыгрышей не найдено.")
    else:
        for record in giveaways:
            text = f'<a href="{record["link"]}">{record["channeltitle"]}</a> — {record["giveawaydate"]}'
            await message.reply(text, disable_web_page_preview=True, parse_mode=ParseMode.HTML)


@bot_app.on_message(filters.command("all"))
async def all_handler(client, message):
    giveaways = await get_future_giveaways()
    if not giveaways:
        await message.reply("Будущих розыгрышей не найдено.")
        return

    batch_size = 10
    chunks = [giveaways[i:i + batch_size] for i in range(0, len(giveaways), batch_size)]

    for chunk in chunks:
        lines = [f'<a href="{rec["link"]}">{rec["channeltitle"]}</a> — {rec["giveawaydate"]}' for rec in chunk]
        text = "\n".join(lines)
        await message.reply(text, disable_web_page_preview=True, parse_mode=ParseMode.HTML)


@bot_app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply(
        "Бот для поиска розыгрышей запущен!\n"
        "/today — розыгрыши сегодня\n"
        "/all — все будущие"
    )


async def main():
    await db.connect()
    await bot_app.start()
    print("Бот запущен!")
    await bot_app.idle()
    await db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
