import re
from datetime import datetime
from config import REPORT_CHANNEL

def extract_and_send_date(app):
    try:
        channel = "@giveawaybrand"
        chat = app.get_chat(channel)
        last_message = list(app.get_chat_history(chat.id, limit=1))[0]
        
        text = last_message.caption if hasattr(last_message, "caption") else last_message.text if hasattr(last_message, "text") else ""
        if not text:
            app.send_message(REPORT_CHANNEL, "Не удалось извлечь текст из последнего сообщения.")
            return  
        
        match_word_date_time = re.search(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+в\s+(\d{1,2}:\d{2})", text)
        date_str = None  
        
        if match_word_date_time:
            day, month, time_str = match_word_date_time.groups()
            date_str = f"{day} {month} в {time_str}"

        if date_str:
            message = (
                f"Дата - {date_str}\n"
                f"Ссылка - https://t.me/{channel}/{last_message.id}"
            )
            app.send_message(REPORT_CHANNEL, message)
            print(f"Сообщение отправлено:\n{message}")
        else:
            app.send_message(REPORT_CHANNEL, "Дата не найдена в последнем сообщении.")
    except Exception as e:
        print(f"Ошибка: {e}")