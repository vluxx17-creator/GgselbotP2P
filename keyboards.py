from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import MINI_APP_URL

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="📋 Мои сделки", callback_data="my_deals")
        ],
        [
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals"),
            InlineKeyboardButton(text="🌐 Язык / Lang", callback_data="language")
        ],
        [
            InlineKeyboardButton(text="🛠 Техподдержка", callback_data="support"),
            InlineKeyboardButton(text="🌍 Открыть GGSel", web_app=dict(url=MINI_APP_URL))
        ],
        [
            InlineKeyboardButton(text="📱 Мини-приложение", web_app=dict(url=MINI_APP_URL))
        ]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Завершить сделку", callback_data="admin_complete_deal"),
            InlineKeyboardButton(text="💳 Выдать баланс", callback_data="admin_give_balance")
        ],
        [
            InlineKeyboardButton(text="👑 Выдать админа", callback_data="admin_give_admin"),
            InlineKeyboardButton(text="👑 Снять админа", callback_data="admin_remove_admin")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📨 Сообщения поддержки", callback_data="admin_support_messages")
        ],
        [
            InlineKeyboardButton(text="❌ Закрыть", callback_data="close_admin")
        ]
    ])

def back_to_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="admin_back")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])
