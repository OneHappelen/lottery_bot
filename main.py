from pyrogram import Client
import time
import os
from dotenv import load_dotenv
import time
from datetime import datetime
import sqlite3


load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME")

app = Client(session_name, api_id=api_id, api_hash=api_hash)




groups = ['@Wylsared', '@moscowach', '@whackdoor', '@trendsetter', '@rozetkedlive', '@rozetked', '@retailrus', '@Romancev768', '@b_retail', '@bezposhady',
'@remedia', '@zubarefff', '@provod', '@mosnoow', '@biggeekru', '@TrendWatching24', '@unit_ru', '@thearseny', '@filatovTIMES', '@stopgameru',
'@trendach', '@mknewsru', '@settersmedia_news', '@intelligent_cat', 'https://t.me/+iI538bjZlGJmYWQy', '@jeteed', '@igmtv', '@mosreview',
'@ruspr', '@trends', '@setters', '@techmedia', '@technopark_ru', '@AuroraTeam', '@bigpencil', '@mosguru', '@moscowmi', '@techbybird', '@technodeus2023',
'@klientvsprav', '@rbtshki', '@bugfeature', '@exploitex', '@techno_yandex', '@zhiga', '@yandex', '@topor', '@dvizhitall', '@pekagame', '@moscowachplus',
'@nebudetgg', '@moscowmap', '@pravdadirty', '@infomoscow24', '@rhymestg', '@lifegoodd1', '@codecamp', '@malepeg', '@xor_journal', '@colizeumarena',
'@rhymesport', '@Match_TV', '@sportsru', '@news_matchtv', '@Inter_sh0p', '@sports_kiber']



# Функция для работы с базой данных
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



def check_and_add_message(cursor,chat_id, message_id):
    cursor.execute("SELECT 1 FROM Forward_ID WHERE ChatID = ? AND MessageID = ?", (chat_id, message_id,))
    result = cursor.fetchone()
    
    if result:
        return True
    else:
        cursor.execute("INSERT INTO Forward_ID (ChatID, MessageID) VALUES (?, ?)", (chat_id, message_id,))
        return False



def find_contest(channel):
    words = ["Участвую", "Участвовать"]
    connection, cursor = manage_db_connection()

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
                                        time.sleep(3)
                                    else:
                                        print("Такое сообщение уже есть в @giveawaybrand пропуск.")
                                    
        except Exception as e:
            print(f"Ошибка при обработке группы {group}: {e}")
    connection.commit()
    cursor.close()
    connection.close()


target_hours = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

with app:
    try:
        while True:
            now_time = datetime.now()
            if now_time.hour in target_hours:
                find_contest(groups)
                print('Ждем след часа')
                time.sleep(1800)
            else:
                time.sleep(7*3600)
    finally:
        print("Работа завершена")