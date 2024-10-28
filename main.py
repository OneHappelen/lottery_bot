from pyrogram import Client
import time
import os
from dotenv import load_dotenv
import time
from datetime import datetime


load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME")

app = Client(session_name, api_id=api_id, api_hash=api_hash)

groups = ['@Wylsared', '@moscowach', '@whackdoor', '@trendsetter', '@rozetkedlive', '@rozetked', '@retailrus', '@Romancev768', '@b_retail', '@bezposhady',
'@remedia', '@zubarefff', '@provod', '@mosnoow', '@biggeekru', '@TrendWatching24', '@droidergram', '@unit_ru', '@thearseny', '@filatovTIMES', '@stopgameru',
'@trendach', '@mknewsru', '@dbeskromny', '@settersmedia_news', '@intelligent_cat', 'https://t.me/+iI538bjZlGJmYWQy', '@jeteed', '@igmtv', '@mosreview',
'@ruspr', '@trends', '@setters', '@techmedia', '@technopark_ru', '@AuroraTeam', '@bigpencil']

def find_contest(channel):
    words = ["Участвую", "Участвовать"]
    for group in channel:
        try:
            chat = app.get_chat(group)
            chat_history = list(app.get_chat_history(chat.id, limit=7))
            for message in chat_history:
                if hasattr(message, "reply_markup") and message.reply_markup is not None:
                    for row in message.reply_markup.inline_keyboard:
                        for button in row:
                            if any(word in button.text for word in words):
                                print("Найдено сообщение с кнопкой для участия.")
                                
                                # Проверка на наличие похожего сообщения в группе @VitalSkam
                                existing_messages = app.search_messages('@lottery_russia', query=message.caption or '', limit=1)
                                is_duplicate = any(msg.caption == message.caption for msg in existing_messages)
                                
                                if not is_duplicate:
                                    app.forward_messages('@lottery_russia', chat.id, message.id)
                                    print("Сообщение отправлено в @lottery_russia.")
                                    time.sleep(3)
                                else:
                                    print("Такое сообщение уже есть в @lottery_russia пропуск.")
                                    
        except Exception as e:
            print(f"Ошибка при обработке группы {group}: {e}")


target_hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

with app:
    while True:
        now_time = datetime.now()
        if now_time.hour in target_hours:
            find_contest(groups)
            time.sleep(3600)
            print('Ждем след часа')
        else:
            time.sleep(10*3600)