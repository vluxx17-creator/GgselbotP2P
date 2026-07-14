import sqlite3
from typing import Optional, List, Dict, Any

DB_NAME = "data.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # Таблица пользователей
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            balance INTEGER DEFAULT 0,
            referral_id INTEGER,
            success_deals INTEGER DEFAULT 0,
            language TEXT DEFAULT 'ru',
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица сделок
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memo TEXT UNIQUE NOT NULL,
            seller_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            commission INTEGER DEFAULT 0,
            chat_messages_count INTEGER DEFAULT 0,
            FOREIGN KEY (seller_id) REFERENCES users(id),
            FOREIGN KEY (buyer_id) REFERENCES users(id)
        )
    """)
    
    # Таблица рефералов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            referred_user_id INTEGER NOT NULL,
            earned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (referred_user_id) REFERENCES users(id)
        )
    """)
    
    # Таблица сообщений поддержки
    cur.execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_answered BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Таблица транзакций
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            description TEXT,
            deal_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """)
    
    conn.commit()
    conn.close()

# ===== ПОЛЬЗОВАТЕЛИ =====
def get_or_create_user(telegram_id: int, username: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        if username:
            cur.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
            conn.commit()
        conn.close()
        return user_id
    else:
        cur.execute("INSERT INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

def update_user_balance(user_id: int, amount: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_user_balance(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

def increase_success_deals(user_id: int, increment: int = 1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET success_deals = success_deals + ? WHERE id = ?", (increment, user_id))
    conn.commit()
    conn.close()

def set_admin_status(user_id: int, is_admin: bool):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if is_admin else 0, user_id))
    conn.commit()
    conn.close()

def get_all_admins():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE is_admin = 1")
    rows = cur.fetchall()
    conn.close()
    if rows:
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    return []

# ===== СДЕЛКИ =====
def create_deal(seller_id: int, buyer_id: int, amount: int, currency: str, memo: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO deals (seller_id, buyer_id, amount, currency, memo)
        VALUES (?, ?, ?, ?, ?)
    """, (seller_id, buyer_id, amount, currency, memo))
    conn.commit()
    deal_id = cur.lastrowid
    conn.close()
    return deal_id

def get_deal_by_memo(memo: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM deals WHERE memo = ?", (memo,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

def get_deal_by_id(deal_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))
    return None

def update_deal_status(deal_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE deals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, deal_id))
    conn.commit()
    conn.close()

def complete_deal(deal_id: int):
    """Завершить сделку и начислить деньги продавцу"""
    conn = get_connection()
    cur = conn.cursor()
    deal = get_deal_by_id(deal_id)
    if not deal:
        conn.close()
        return False
    
    commission = int(deal['amount'] * 0.05)
    seller_payout = deal['amount'] - commission
    
    cur.execute("UPDATE deals SET status = 'completed', completed_at = CURRENT_TIMESTAMP, commission = ? WHERE id = ?", 
                (commission, deal_id))
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (seller_payout, deal['seller_id']))
    cur.execute("UPDATE users SET success_deals = success_deals + 1 WHERE id = ?", (deal['seller_id'],))
    cur.execute("UPDATE users SET success_deals = success_deals + 1 WHERE id = ?", (deal['buyer_id'],))
    
    # Записываем транзакцию
    cur.execute("""
        INSERT INTO transactions (user_id, amount, transaction_type, description, deal_id)
        VALUES (?, ?, ?, ?, ?)
    """, (deal['seller_id'], seller_payout, 'payment', f'Оплата по сделке #{deal["memo"]}', deal_id))
    
    # Начисляем реферальные бонусы
    seller = get_user_by_id(deal['seller_id'])
    if seller and seller['referral_id']:
        referral_bonus = int(commission * 0.5)
        cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (referral_bonus, seller['referral_id']))
        cur.execute("INSERT INTO referrals (user_id, referred_user_id, earned) VALUES (?, ?, ?)", 
                    (seller['referral_id'], deal['seller_id'], referral_bonus))
    
    conn.commit()
    conn.close()
    return True

def get_user_deals(user_id: int, status: str = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute("""
            SELECT * FROM deals 
            WHERE (seller_id = ? OR buyer_id = ?) AND status = ?
            ORDER BY created_at DESC
        """, (user_id, user_id, status))
    else:
        cur.execute("""
            SELECT * FROM deals 
            WHERE seller_id = ? OR buyer_id = ?
            ORDER BY created_at DESC
        """, (user_id, user_id))
    rows = cur.fetchall()
    conn.close()
    if rows:
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    return []

# ===== РЕФЕРАЛЫ =====
def add_referral(user_id: int, referred_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO referrals (user_id, referred_user_id) VALUES (?, ?)", (user_id, referred_id))
    conn.commit()
    conn.close()

def get_referral_earnings(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(earned) FROM referrals WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row[0] else 0

def get_referrals(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.*, r.earned, r.created_at 
        FROM referrals r
        JOIN users u ON r.referred_user_id = u.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    if rows:
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    return []

# ===== ПОДДЕРЖКА =====
def add_support_message(user_id: int, text: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO support_messages (user_id, message_text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    conn.close()

def user_has_support_message(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM support_messages WHERE user_id = ? LIMIT 1", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def get_unanswered_support_messages():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM support_messages 
        WHERE is_answered = 0 
        ORDER BY created_at ASC
    """)
    rows = cur.fetchall()
    conn.close()
    if rows:
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    return []

def mark_support_as_answered(message_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE support_messages SET is_answered = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

# ===== ТРАНЗАКЦИИ =====
def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM transactions 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    if rows:
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    return []
