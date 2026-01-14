import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="crypto_bot.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                subscribed BOOLEAN DEFAULT 1,
                subscription_date TIMESTAMP,
                last_active TIMESTAMP
            )
        ''')
        
        # Таблица статистики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                date DATE,
                messages_sent INTEGER,
                new_subscribers INTEGER,
                active_users INTEGER
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, subscribed, subscription_date, last_active)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            ''', (user_id, username, first_name, last_name, datetime.now(), datetime.now()))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False
    
    def get_subscribers(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE subscribed = 1')
        return [row[0] for row in cursor.fetchall()]
    
    def update_stats(self, messages_sent):
        cursor = self.conn.cursor()
        today = datetime.now().date()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stats (date, messages_sent, new_subscribers, active_users)
            VALUES (?, COALESCE((SELECT messages_sent FROM stats WHERE date = ?), 0) + ?,
                   (SELECT COUNT(*) FROM users WHERE DATE(subscription_date) = ?),
                   (SELECT COUNT(*) FROM users WHERE subscribed = 1))
        ''', (today, today, messages_sent, today))
        
        self.conn.commit()