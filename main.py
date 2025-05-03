from pyrogram import Client
import time
import os
from dotenv import load_dotenv
import time
from datetime import datetime
import sqlite3
import re


load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME")

app = Client(session_name, api_id=api_id, api_hash=api_hash)




groups = ['@Wylsared', '@moscowach', '@whackdoor', '@trendsetter', '@rozetkedlive', '@rozetked', '@retailrus', '@Romancev768', '@b_retail', '@bezposhady',
'@remedia', '@zubarefff', '@provod', '@mosnews', '@biggeekru', '@TrendWatching24', '@unit_ru', '@thearseny', '@stopgameru',
'@trendach', '@mknewsru', '@settersmedia_news', '@intelligent_cat', 'https://t.me/+iI538bjZlGJmYWQy', '@jeteed', '@igmtv', '@mosreview',
'@ruspr', '@trends', '@setters', '@techmedia', '@technopark_ru' '@bigpencil', '@mosguru', '@moscowmi', '@techbybird', '@technodeus2023',
'@klientvsprav', '@rbtshki', '@bugfeature', '@exploitex', '@techno_yandex', '@zhiga', '@yandex', '@topor', '@dvizhitall', 't.me/+VIuvvPWhb-mR4BRq', '@moscowachplus',
'@nebudetgg', '@moscowmap', '@pravdadirty', '@infomoscow24', '@rhymestg', '@lifegoodd1', '@codecamp', '@malepeg', '@xor_journal', '@colizeumarena',
'@rhymesport', '@Match_TV', '@sportsru', '@news_matchtv', '@Inter_sh0p', '@sports_kiber', '@investingcorp', '@Moscow_happy', '@luka_ebkov', '@OneBoxTwoBox',
'@Technical_R_D', '@rostov_glavniy', '@tochnokosmos', '@msk7days', '@mrnickstore', '@nechetoff', '@ryanrun', '@boomers_TV', '@oplata_skoro_budet', '@kostylofficial']



"""
Функция для управления соединением с базой данных SQLite

"""
def manage_db_connection():
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()
    
    # Создаем таблицу с уникальным идентификатором сообщения
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Forward_ID (
        ChatID INTEGER NOT NULL,
        MessageID INTEGER NOT NULL,
        UNIQUE(ChatID, MessageID)
    )
    ''')
    
    connection.commit()
    return connection, cursor

"""
Функция для проверки наличия сообщения в базе данных и добавления его, если его там нет
"""

def check_and_add_message(cursor,chat_id, message_id):
    cursor.execute("SELECT 1 FROM Forward_ID WHERE ChatID = ? AND MessageID = ?", (chat_id, message_id,))
    result = cursor.fetchone()
    
    if result:
        return True
    else:
        cursor.execute("INSERT INTO Forward_ID (ChatID, MessageID) VALUES (?, ?)", (chat_id, message_id,))
        return False

"""
Функция для извлечения даты и времени из сообщения и отправки в @dategiveaway

"""
def extract_and_send_date():
    try:
        # Получаем последний пост из канала @giveawaybrand
        channel = "@giveawaybrand"
        chat = app.get_chat(channel)
        last_message = list(app.get_chat_history(chat.id, limit=1))[0]
        
        # Извлечение текста из caption или text
        text = ""
        if hasattr(last_message, "caption") and last_message.caption:
            text = last_message.caption
        elif hasattr(last_message, "text") and last_message.text:
            text = last_message.text
        
        if not text:
            app.send_message("@dategiveaway", "Не удалось извлечь текст из последнего сообщения.")
            return  
        
        # Поиск даты и времени в различных форматах
        match_word_date_time = re.search(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+в\s+(\d{1,2}:\d{2})", text)
        match_word_date = re.search(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)", text)
        match_numeric_date_time = re.search(r"(\d{2})\.(\d{2})\.(\d{2,4})\s+в\s+(\d{1,2}:\d{2})", text)
        match_numeric_date = re.search(r"(\d{2})\.(\d{2})\.(\d{2,4})", text)
        
        date_str = None  # Для хранения отформатированной строки даты
        
        if match_word_date_time:
            # Формат "день месяц в часы:минуты"
            day, month, time_str = match_word_date_time.groups()
            date_str = f"{day} {month} в {time_str}"
        elif match_word_date:
            # Формат "день месяц"
            day, month = match_word_date.groups()
            date_str = f"{day} {month}"
        elif match_numeric_date_time:
            # Формат "дд.мм.гг в часы:минуты"
            day, month, year, time_str = match_numeric_date_time.groups()
            date_str = f"{day}.{month}.{year} в {time_str}"
        elif match_numeric_date:
            # Формат "дд.мм.гг"
            day, month, year = match_numeric_date.groups()
            date_str = f"{day}.{month}.{year}"

        if hasattr(last_message, "forward_from_chat") and last_message.forward_from_chat:
            forward_chat = last_message.forward_from_chat

            # Извлекаем данные из объекта
            chat_title = forward_chat.title    
        
        if date_str:
            # Формируем сообщение
            message = (
                f"Дата - {date_str}\n"
                f"Канал - {chat_title}\n"
                f"Ссылка - https://t.me/{channel}/{last_message.id}"
            )
            
            # Отправляем сообщение в @dategiveaway
            app.send_message("@dategiveaway", message)
            print(f"Сообщение отправлено:\n{message}")
        else:
            app.send_message("@dategiveaway", "Дата не найдена в последнем сообщении.")
            print("Дата не найдена в последнем сообщении.")
    except Exception as e:
        print(f"Ошибка: {e}")


"""
Функция для поиска розыгрышей в каналах и пересылки их в @giveawaybrand
"""

def find_contest(channel):
    words = ["Участвую", "Участвовать"]
    connection, cursor = manage_db_connection()
    count_contest = 0

    for group in channel:
        try:
            time.sleep(1)
            print(f"Канал {group} в процессе")
            chat = app.get_chat(group)
            chat_history = list(app.get_chat_history(chat.id, limit=7))
            for message in chat_history:
                if hasattr(message, "reply_markup") and message.reply_markup is not None:
                    for row in message.reply_markup.inline_keyboard:
                        for button in row:
                            if any(word in button.text for word in words):
                                print("Найдено сообщение с кнопкой для участия.")
                                
                                # Проверка на наличие похожего сообщения в группе @VitalSkam
                                message_id = message.id
                                if message_id is not None:
                                    is_duplicate = check_and_add_message(cursor,chat.id, message_id)
                                    
                                    if not is_duplicate:
                                        app.forward_messages('@giveawaybrand', chat.id, message.id)
                                        print("Сообщение отправлено в @giveawaybrand.")
                                        count_contest += 1
                                        extract_and_send_date()
                                        time.sleep(3)
                                    else:
                                        print("Такое сообщение уже есть в @giveawaybrand пропуск.")
                                    
        except Exception as e:
            print(f"Ошибка при обработке группы {group}: {e}")
    connection.commit()
    cursor.close()
    connection.close()
    return count_contest

"""
Функция для отправки отчета в @dategiveaway
"""
def send_final_report(count_contest):
    try:
        report_message = f"Итоги за сегодня:\nНайдено розыгрешей: {count_contest}"
        app.send_message("@dategiveaway", report_message)
        print(f"Отсчет доставлен: {report_message}")
    except Exception as e:
        print(f"Ошибка при отправке отчета: {e}")     


target_hours = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

total_contests = 0


"""
Запуск бота и ожидание сообщений

"""

with app:
    try:
        while True:
            now_time = datetime.now()
            if now_time.hour in target_hours:
                found_today = find_contest(groups)
                total_contests += found_today
                print('Ждем следующей проверки...')
                time.sleep(1800)
            else:
                send_final_report(total_contests)
                total_contests = 0
                time.sleep(7*3600)
    finally:
        print("Работа завершена")