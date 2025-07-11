import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sqlite3
import re
from pyrogram import Client
from pyrogram.types import Message
from typing import Set

# Папка проекта — родительская для user_bot
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Путь к базе данных: папка_проекта/bd/giveaways.db
DB_DIR = os.path.join(PROJECT_DIR, "bd")
DB_PATH = os.path.join(DB_DIR, "giveaways.db")

# Убедимся, что папка для БД существует
os.makedirs(DB_DIR, exist_ok=True)

load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
user_app = Client("user_session", api_id=api_id, api_hash=api_hash)

# Пути к файлам groups.txt и new_group.txt в корне проекта
GROUPS_FILE = os.path.join(PROJECT_DIR, "groups.txt")
NEW_GROUPS_FILE = os.path.join(PROJECT_DIR, "new_group.txt")

# groups = [
#     '@Wylsared', '@moscowach', '@whackdoor', '@trendsetter', '@rozetkedlive', '@rozetked', '@retailrus', '@Romancev768', '@b_retail', '@bezposhady',
#     '@remedia', '@zubarefff', '@provod', '@mosnews', '@biggeekru', '@TrendWatching24', '@unit_ru', '@thearseny', '@stopgameru',
#     '@trendach', '@mknewsru', '@settersmedia_news', '@intelligent_cat', 'https://t.me/+iI538bjZlGJmYWQy', '@jeteed', '@igmtv', '@mosreview',
#     '@ruspr', '@trends', '@setters', '@techmedia', '@technopark_ru', '@bigpencil', '@mosguru', '@moscowmi', '@techbybird', '@technodeus2023',
#     '@klientvsprav', '@rbtshki', '@bugfeature', '@exploitex', '@techno_yandex', '@zhiga', '@yandex', '@topor', '@dvizhitall', 't.me/+VIuvvPWhb-mR4BRq', '@moscowachplus',
#     '@nebudetgg', '@moscowmap', '@pravdadirty', '@infomoscow24', '@rhymestg', '@lifegoodd1', '@codecamp', '@malepeg', '@xor_journal', '@colizeumarena',
#     '@rhymesport', '@Match_TV', '@sportsru', '@news_matchtv', '@Inter_sh0p', '@sports_kiber', '@investingcorp', '@Moscow_happy', '@luka_ebkov', '@OneBoxTwoBox',
#     '@Technical_R_D', '@rostov_glavniy', '@tochnokosmos', '@msk7days', '@mrnickstore', '@nechetoff', '@ryanrun', '@boomers_TV', '@oplata_skoro_budet', '@kostylofficial',
#     '@citilink_official', '@evgenmt'
# ]


def add_text_column_if_not_exists():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Получаем список колонок таблицы Giveaways
    c.execute("PRAGMA table_info(Giveaways)")
    columns = [info[1] for info in c.fetchall()]

    # Если колонки Text нет — добавляем
    if "Text" not in columns:
        c.execute("ALTER TABLE Giveaways ADD COLUMN Text TEXT")
        print("Колонка 'Text' добавлена в таблицу Giveaways.")
    else:
        print("Колонка 'Text' уже существует.")

    conn.commit()
    conn.close()


# --------------- База данных ---------------
def add_text_column_if_not_exists(conn):
    c = conn.cursor()
    c.execute("PRAGMA table_info(Giveaways)")
    columns = [info[1] for info in c.fetchall()]

    if "Text" not in columns:
        c.execute("ALTER TABLE Giveaways ADD COLUMN Text TEXT")
        print("Колонка 'Text' добавлена в таблицу Giveaways.")
    else:
        print("Колонка 'Text' уже существует.")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS Giveaways (
        ChatID INTEGER,
        MessageID INTEGER,
        Link TEXT,
        ChannelTitle TEXT,
        GiveawayDate TEXT,
        PRIMARY KEY(ChatID, MessageID)
    )''')

    # Проверяем и добавляем колонку Text, если нужно
    add_text_column_if_not_exists(conn)

    conn.commit()
    conn.close()



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
def add_giveaway(chat_id, message_id, link, channel_title, giveaway_date, text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Проверяем, есть ли запись с таким ChatID и MessageID
    c.execute("SELECT 1 FROM Giveaways WHERE ChatID = ? AND MessageID = ?", (chat_id, message_id))
    if c.fetchone():
        print("Сообщение с таким ChatID и MessageID уже есть в базе, пропуск.")
        conn.close()
        return

    # Если нет — проверяем, есть ли запись с таким же текстом
    c.execute("SELECT 1 FROM Giveaways WHERE Text = ?", (text,))
    if c.fetchone():
        print("Сообщение с таким же текстом уже есть в базе, пропуск.")
        conn.close()
        return

    # Обработка даты
    parsed_date = parse_giveaway_date(giveaway_date)
    if parsed_date:
        giveaway_date_str = parsed_date.strftime("%Y-%m-%d")
    else:
        giveaway_date_str = giveaway_date

    # Добавляем новую запись
    c.execute('''
        INSERT INTO Giveaways (ChatID, MessageID, Link, ChannelTitle, GiveawayDate, Text)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (chat_id, message_id, link, channel_title, giveaway_date_str, text))

    conn.commit()
    conn.close()

# Очистка устаревших розыгрышей
def cleanup_old_giveaways():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    #получаю все розыгрыши по полям ChatID, MessageID, GiveawayDate и помещаю в rows
    c.execute('SELECT ChatID, MessageID, GiveawayDate FROM Giveaways')
    rows = c.fetchall()

    today = datetime.now().date() # получаю текущую дату
    deleted = 0

    #прохожу по всем розыгрышам и проверяю дату с сегодняшней
    for chat_id, msg_id, raw_date in rows:
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            #если дата розыгрыша меньше сегодняшней
            if parsed_date < today:
                #удаляю из бд
                c.execute('DELETE FROM Giveaways WHERE ChatID=? AND MessageID=?', (chat_id, msg_id))
                deleted += 1
        except ValueError:
            # Игнорируем строки, которые не удалось распарсить
            continue

    conn.commit()
    conn.close()
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

    for group in groups.copy():  # Используем .copy() чтобы избежать RuntimeError при итерации
        try:
            await asyncio.sleep(2) #жди секунду
            print(f"Канал {group} в процессе")
            chat = await user_app.get_chat(group) #получаю обьект чата группы N

            async for message in user_app.get_chat_history(chat.id, limit=7): #получаю последние 7 постов в канале
                if hasattr(message, "reply_markup") and message.reply_markup is not None: #проверяю есть ли у поста reply_markup и не являеться ли он None
                    for row in message.reply_markup.inline_keyboard: #прохожу по списку кнопок с посте
                        for button in row:
                            if any(word in button.text for word in words):# делаю проверку на слово Учавствовать у кнопки
                                print("Найдено сообщение с кнопкой для участия.")
                                message_id = message.id
                                if message_id is not None:
                                    # Проверка в БД есть ли такая запись уже сравнивая chat.id и message.id
                                    conn = sqlite3.connect(DB_PATH)
                                    c = conn.cursor()
                                    c.execute("SELECT 1 FROM Giveaways WHERE ChatID=? AND MessageID=?", (chat.id, message_id))
                                    exists = c.fetchone()
                                    conn.close()

                                    if exists:
                                        print("Такое сообщение уже есть в базе, пропуск.")
                                        continue

                                    text = getattr(message, "caption", "") or getattr(message, "text", "") or "" #извлекаю текст из text или caption
                                    entities = getattr(message, "caption_entities", None) or getattr(message, "entities", None) #извлекаю разметку текста в поисках ссылок на др. каналы

                                    giveaway_date = extract_giveaway_date(text) # извлекаю дату из текста сообщения
                                    await send_giveaway_date_info(chat, message_id, giveaway_date) # отправляю дату и ссылку в отсчетный канал

                                    link = f"https://t.me/{chat.username}/{message_id}" if getattr(chat, "username", None) else "" #формирую ссылку на розыгрыш в родительском канале
                                    channel_title = getattr(chat, "title", "")# извлекаю название канала

                                    add_giveaway(chat.id, message_id, link, channel_title, giveaway_date or "не указана", text)#добавляю в бд извлеченные данные
                                    await user_app.forward_messages('@giveawaybrand', chat.id, message.id)#пересылаю в целевой канал сообщение с розыгрешем

                                    # Извлекаем и сохраняем новые группы
                                    extract_and_save_new_groups(text, groups, entities)

                                    print("Сообщение отправлено в @giveawaybrand и добавлено в БД.")
                                    count_contest += 1
                                    await asyncio.sleep(3)
            await asyncio.sleep(2)                          
        except Exception as e:
            print(f"Ошибка при обработке группы {group}: {e}")

    return count_contest

async def userbot_worker():
    init_db()
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
            cleanup_old_giveaways()#удаление устаревших розыгрышей по дате 
            await asyncio.sleep(7*3600)

async def main():
    init_db()
    async with user_app:
        asyncio.create_task(userbot_worker())
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())