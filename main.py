from bot import app, find_contest, send_final_report
from config import GROUPS
from datetime import datetime
import time

# Часы, в которые нужно запускать процесс
target_hours = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
total_contests = 0  # Счетчик розыгрышей

with app:
    try:
        while True:
            now_time = datetime.now()
            if now_time.hour in target_hours:
                found_today = find_contest(GROUPS)
                total_contests += found_today
                print('Ждем следующей проверки...')
                time.sleep(1800)
            else:
                send_final_report(total_contests)
                total_contests = 0
                time.sleep(7 * 3600)
    finally:
        print("Работа завершена")