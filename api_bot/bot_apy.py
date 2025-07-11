import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ParseMode

# Загрузка переменных окружения
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# Путь к базе данных в папке bd
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bd", "giveaways.db")

bot_app = Client("bot_session", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


# Функция для парсинга даты розыгрыша из базы данных
def parse_giveaway_datetime(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


# Получение розыгрышей на сегодня
def get_today_giveaways():
    today_str = datetime.now().strftime("%Y-%m-%d") #получаю текущую дату
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT Link, ChannelTitle, GiveawayDate FROM Giveaways WHERE GiveawayDate = ?", (today_str,)) #запрашиваю ссылку, название канала и дату и фильрую относительно сегодняшней даты
    rows = c.fetchall() #помещаю данные в(если есть) в переменую
    conn.close()
    return rows

# Получение будущих розыгрышей
def get_future_giveaways():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT Link, ChannelTitle, GiveawayDate FROM Giveaways") #запрашиваю ссылку, название канала и дату(все что есть в бд)
    rows = c.fetchall() #помещаю в переменную
    conn.close()

    now_date = datetime.now().date() #получаю сегодняшнюю дату
    future_rows = []

    for link, title, date_str in rows:
        dt = parse_giveaway_datetime(date_str) #приводи дату к единому формату
        if dt and dt.date() >= now_date:#делаем проверку на актуальность требованиям даты
            future_rows.append((link, title, date_str, dt)) #кидаю в список ссылку, название канала, строка даты, обьект datetime 

    future_rows.sort(key=lambda x: x[3]) #сортирую розыгрыши по дате от самое ближней и далее
    return [(link, title, date_str) for link, title, date_str, _ in future_rows]


# Обработчик команды /today
@bot_app.on_message(filters.command("today"))
async def today_handler(client, message):
    giveaways = get_today_giveaways() #получаю розыгрыши с сегодняшней датой
    if not giveaways:
        await message.reply("Сегодня розыгрышей не найдено.") #отвечаю если их нет
    else:
        for link, title, date in giveaways:
            # Формируем ссылку с названием канала в HTML формате
            text = f'<a href="{link}">{title}</a> — {date}'
            await message.reply(text, disable_web_page_preview=True, parse_mode="html") #отправляю по порядку все розыгрыши с сегодняшней датой

# Обработчик команды /all
@bot_app.on_message(filters.command("all"))
async def all_handler(client, message):
    giveaways = get_future_giveaways() # получаю данные о розыгрышах если есть
    if not giveaways:
        await message.reply("Будущих розыгрышей не найдено.")
        return

    batch_size = 10 #задаю лимит для строк в сообщении
    chunks = [giveaways[i:i + batch_size] for i in range(0, len(giveaways), batch_size)] #формирую первую порцию данных из 10 строк

    #отправляю сообщения пользователю по 10 строк в каждом с ссылкой в названии на розыгрыш и датой
    for chunk in chunks:
        lines = []
        for link, title, date in chunk:
            lines.append(f'<a href="{link}">{title}</a> — {date}')
        text = "\n".join(lines)
        await message.reply(text, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

# Обработчик команды /start
@bot_app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply("Бот для поиска розыгрышей запущен! /today — розыгрыши сегодня, /all — все будущие.")

if __name__ == "__main__":
    bot_app.run()