import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

def manage_db_connection():
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Forward_ID (
        ChatID INTEGER NOT NULL,
        MessageID INTEGER NOT NULL,
        Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        Month TEXT NOT NULL,
        UNIQUE(ChatID, MessageID)
    )
    ''')
    
    connection.commit()
    return connection, cursor

def check_and_add_message(cursor, chat_id, message_id):
    cursor.execute("SELECT 1 FROM Forward_ID WHERE ChatID = ? AND MessageID = ?", (chat_id, message_id))
    result = cursor.fetchone()
    
    if result:
        return True
    else:
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute(
            "INSERT INTO Forward_ID (ChatID, MessageID, Month) VALUES (?, ?, ?)",
            (chat_id, message_id, current_month)
        )
        return False

def clean_old_entries(cursor):
    # Оставляем данные за последние 3 месяца
    months_to_keep = [
        (datetime.now() - relativedelta(months=i)).strftime("%Y-%m")
        for i in range(3)
    ]
    placeholder = ','.join(['?'] * len(months_to_keep))
    
    cursor.execute(f'''
        DELETE FROM Forward_ID
        WHERE Month NOT IN ({placeholder})
    ''', months_to_keep)
    
    print(f"Удалены записи вне месяцев: {', '.join(months_to_keep)}")