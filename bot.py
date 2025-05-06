from pyrogram import Client
import time
from config import API_ID, API_HASH, SESSION_NAME, FORWARD_CHANNEL, REPORT_CHANNEL
from database import manage_db_connection, check_and_add_message, clean_old_entries
from utils import extract_and_send_date

# Инициализация клиента
app = Client(SESSION_NAME, API_ID, API_HASH)

def find_contest(groups):
    words = ["Участвую", "Участвовать"]
    connection, cursor = manage_db_connection()
    count_contest = 0

    for group in groups:
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
                                
                                message_id = message.id
                                if message_id is not None:
                                    is_duplicate = check_and_add_message(cursor, chat.id, message_id)
                                    
                                    if not is_duplicate:
                                        app.forward_messages(FORWARD_CHANNEL, chat.id, message.id)
                                        print("Сообщение отправлено в @giveawaybrand.")
                                        count_contest += 1
                                        extract_and_send_date(app)
                                        time.sleep(3)
                                    else:
                                        print("Такое сообщение уже есть в @giveawaybrand. Пропуск.")
        except Exception as e:
            print(f"Ошибка при обработке группы {group}: {e}")

    clean_old_entries(cursor)        
    connection.commit()
    cursor.close()
    connection.close()
    return count_contest

def send_final_report(count_contest):
    try:
        report_message = f"Итоги за сегодня:\nНайдено розыгрышей: {count_contest}"
        app.send_message(REPORT_CHANNEL, report_message)
        print(f"Отчет доставлен: {report_message}")
    except Exception as e:
        print(f"Ошибка при отправке отчета: {e}")