import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import sys
from pyrogram import Client
from pyrogram.types import Message
from typing import Set



# Папка проекта — родительская для user_bot
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_pool, Database

load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
user_app = Client("user_session", api_id=api_id, api_hash=api_hash)

# Пути к файлам groups.txt и new_group.txt в корне проекта
GROUPS_FILE = os.path.join(PROJECT_DIR, "groups.txt")
NEW_GROUPS_FILE = os.path.join(PROJECT_DIR, "new_group.txt")




# --------------- База данных ---------------







# Парсинг даты розыгрыша для дальнейшего приведения к единому формату
def parse_giveaway_date(raw_date: str) -> datetime | None:
    raw_date = raw_date.strip().lower()

    # Поддержка формата "12 мая в 15:00"
    match = re.match(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+в\s+(\d{1,2}):(\d{2})", raw_date)
    if match:
        day, month_name, hour, minute = match.groups()
        month = MONTHS_RU.get(month_name)
        if month:
            try:
                year = datetime.now().year
                parsed = datetime(year, month, int(day), int(hour), int(minute))
                if parsed < datetime.now() - timedelta(days=180):
                    parsed = parsed.replace(year=year + 1)
                return parsed
            except:
                return None

    # Поддержка числовой даты с временем: 12.05.2024 в 15:00
    match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s+в\s+(\d{1,2}):(\d{2})", raw_date)
    if match:
        day, month, year, hour, minute = match.groups()
        year = int(year)
        if year < 100:
            year += 2000
        try:
            return datetime(year, int(month), int(day), int(hour), int(minute))
        except:
            return None

    # Поддержка числовой даты без времени
    match = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", raw_date)
    if match:
        day, month, year = match.groups()
        year = int(year)
        if year < 100:
            year += 2000
        try:
            return datetime(year, int(month), int(day))
        except:
            return None

    # Поддержка словесной даты без времени: "12 мая"
    match = re.match(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)", raw_date)
    if match:
        day, month_name = match.groups()
        month = MONTHS_RU.get(month_name)
        if month:
            try:
                year = datetime.now().year
                parsed = datetime(year, month, int(day))
                if parsed < datetime.now() - timedelta(days=180):
                    parsed = parsed.replace(year=year + 1)
                return parsed
            except:
                return None

    return None


# Добавление розыгрыша в базу данных
async def add_giveaway(chat_id, message_id, link, channel_title, giveaway_date, text):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Проверка на дубликат по тексту
        existing = await conn.fetchrow(
            "SELECT 1 FROM giveaways WHERE text = $1",
            text
        )
        if existing:
            print("❌ Сообщение с таким же текстом уже есть в базе, пропуск.")
            return False

        # Обработка даты
        parsed_date = parse_giveaway_date(giveaway_date)
        giveaway_date_str = parsed_date.strftime("%Y-%m-%d") if parsed_date else giveaway_date

        # Вставка новой записи
        await conn.execute('''
            INSERT INTO giveaways (chat_id, message_id, link, channel_title, giveaway_date, text)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', chat_id, message_id, link, channel_title, giveaway_date_str, text)

        print("✅ Новая запись успешно добавлена.")
        return True



# Очистка устаревших розыгрышей
async def cleanup_old_giveaways():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT ChatID, MessageID, GiveawayDate FROM Giveaways')

        today = datetime.now().date()
        deleted = 0

        for row in rows:
            try:
                parsed_date = datetime.strptime(row['GiveawayDate'], "%Y-%m-%d").date()
                if parsed_date < today:
                    await conn.execute(
                        'DELETE FROM Giveaways WHERE ChatID = $1 AND MessageID = $2',
                        row['ChatID'], row['MessageID']
                    )
                    deleted += 1
            except ValueError:
                continue  # Пропускаем записи с некорректной датой

        print(f"Очистка завершена: удалено {deleted} устаревших розыгрышей.")   


MONTHS_RU = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}





# Извлечение даты розыгрыша
def extract_giveaway_date(text):

    # 1. День недели + дата + время
    match_weekday_word_date_time = re.search(
        r"(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)[,]?\s+(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря),?\s+в\s+(\d{1,2}:\d{2})",
        text, re.IGNORECASE
    )

    # 2. Словесная дата с временем (с пробелами или запятыми перед "в")
    match_word_date_time = re.search(
        r"(\d{1,2})(?:-?[гГ][оО]?|[-–]?[еЕ][гоГО]{1,2})?\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)"
        r"(?:\s*,?\s*в\s+)(\d{1,2}:\d{2})",
        text
    )

    # 3. Словесная дата без времени, после "итоги —"
    match_simple_word_date = re.search(
        r"(?:итоги|результаты)[^\n\r\w]{1,3}(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)",
        text, re.IGNORECASE
    )

    # 4. Словесная дата без времени (обычная)
    match_word_date = re.search(
        r"(\d{1,2})(?:-?[гГ][оО]?|[-–]?[еЕ][гоГО]{1,2})?\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)",
        text
    )

    # 5. Числовая дата с временем
    match_numeric_date_time = re.search(
        r"(\d{2})\.(\d{2})\.(\d{2,4})\s+в\s+(\d{1,2}:\d{2})", text
    )

    # 6. Числовая дата без времени
    match_numeric_date = re.search(
        r"(\d{2})\.(\d{2})\.(\d{2,4})", text
    )

    if match_weekday_word_date_time:
        _, day, month, time_str = match_weekday_word_date_time.groups()
        return f"{day} {month} в {time_str}"
    elif match_word_date_time:
        day, month, time_str = match_word_date_time.groups()
        return f"{day} {month} в {time_str}"
    elif match_simple_word_date:
        day, month = match_simple_word_date.groups()
        return f"{day} {month}"
    elif match_word_date:
        day, month = match_word_date.groups()
        return f"{day} {month}"
    elif match_numeric_date_time:
        day, month, year, time_str = match_numeric_date_time.groups()
        return f"{day}.{month}.{year} в {time_str}"
    elif match_numeric_date:
        day, month, year = match_numeric_date.groups()
        return f"{day}.{month}.{year}"
    return None





# Отправка информации о розыгрыше в @dategiveaway
async def send_giveaway_date_info(chat, message_id, giveaway_date):
    # Формируем ссылку на сообщение
    link = f"https://t.me/{chat.username}/{message_id}" if getattr(chat, "username", None) else ""

    # Подготовка текста
    if giveaway_date:
        date_info = f"Дата — {giveaway_date}\nСсылка — {link}"
    else:
        date_info = f"Дата — не найдена\nСсылка — {link}"

    # Отправка в канал
    try:
        await user_app.send_message("@dategiveaway", date_info)
        print("Информация успешно отправлена в @dategiveaway.")
    except Exception as e:
        print(f"Ошибка при отправке в @dategiveaway: {e}")


# Загрузка списка известных групп
def load_group_list(file_path: str) -> Set[str]:
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8"):
            pass
    with open(file_path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

# Сохраняем новую группу
def save_new_group(group_name: str, file_path: str):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(group_name + "\n")

# Извлекаем @каналы и ссылки на них из текста и entities, сохраняем только новые
def extract_and_save_new_groups(
    message_text: str,
    known_groups: Set[str],
    entities: list = None
):
    found_groups = set()

    # Поиск @channelname в тексте
    found_groups.update(re.findall(r"@[\w\d_]{4,32}", message_text))

    # Поиск https://t.me/username в ссылках
    if entities:
        for entity in entities:
            if (
                hasattr(entity, "type") and str(entity.type) == "MessageEntityType.TEXT_LINK"
                and hasattr(entity, "url") and isinstance(entity.url, str)
                and entity.url.startswith("https://t.me/")
            ):
                username = re.sub(r"/.*", "", entity.url.removeprefix("https://t.me/"))
                if username:
                    found_groups.add(f"@{username}")

    # Загружаем уже сохранённые группы из файла
    new_groups = load_group_list(NEW_GROUPS_FILE)

    # Сохраняем только уникальные
    for group in found_groups:
        if group not in known_groups and group not in new_groups:
            print(f"[+] New group found: {group}")
            save_new_group(group, NEW_GROUPS_FILE)
            known_groups.add(group)

# ---------------- Основная логика ----------------
async def find_contest():
    groups = load_group_list(GROUPS_FILE)

    words = ["Участвую", "Участвовать"]
    count_contest = 0

    for group in groups.copy():
        try:
            await asyncio.sleep(2)
            print(f"Канал {group} в процессе")
            chat = await user_app.get_chat(group)

            async for message in user_app.get_chat_history(chat.id, limit=7):
                if hasattr(message, "reply_markup") and message.reply_markup is not None:
                    for row in message.reply_markup.inline_keyboard:
                        for button in row:
                            if any(word in button.text for word in words):
                                print("Найдено сообщение с кнопкой для участия.")
                                message_id = message.id
                                if message_id is not None:

                                    text = getattr(message, "caption", "") or getattr(message, "text", "") or ""
                                    entities = getattr(message, "caption_entities", None) or getattr(message, "entities", None)

                                    giveaway_date = extract_giveaway_date(text)
                                    link = f"https://t.me/{chat.username}/{message_id}" if getattr(chat, "username", None) else ""
                                    channel_title = getattr(chat, "title", "")

                                    added = await add_giveaway(
                                        chat.id,
                                        message_id,
                                        link,
                                        channel_title,
                                        giveaway_date or "не указана",
                                        text
                                    )

                                    if not added:
                                        print("Мы уже добавляли такой розыгрыш")
                                        continue

                                    await send_giveaway_date_info(chat, message_id, giveaway_date)
                                    await user_app.forward_messages('@giveawaybrand', chat.id, message.id)

                                    extract_and_save_new_groups(text, groups, entities)

                                    print("Сообщение отправлено в @giveawaybrand и добавлено в БД.")
                                    count_contest += 1
                                    await asyncio.sleep(3)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Ошибка при обработке группы {group}: {e}")

    return count_contest

async def userbot_worker():
    target_hours = list(range(7, 24))
    total_contests = 0
    while True:
        now_time = datetime.now()
        if now_time.hour in target_hours:
            found_today = await find_contest()
            total_contests += found_today
            print('Ждем следующей проверки...')
            await asyncio.sleep(1800)
        else:
            total_contests = 0
            await cleanup_old_giveaways()  # <-- асинхронная версия
            await asyncio.sleep(7*3600)

async def main():
    async with user_app:
        asyncio.create_task(userbot_worker())
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())