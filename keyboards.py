from telegram import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import MINI_APP_URL

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Баланс", callback_data="balance"),
         InlineKeyboardButton("📋 Мои сделки", callback_data="my_deals")],
        [InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
         InlineKeyboardButton("🌐 Язык / Lang", callback_data="language")],
        [InlineKeyboardButton("🛠 Техподдержка", callback_data="support"),
         InlineKeyboardButton("🌍 Открыть GGSel", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("📱 Мини-приложение", web_app=WebAppInfo(url=MINI_APP_URL))]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Завершить сделку", callback_data="admin_complete_deal"),
         InlineKeyboardButton("💳 Выдать баланс", callback_data="admin_give_balance")],
        [InlineKeyboardButton("👑 Выдать админа", callback_data="admin_give_admin"),
         InlineKeyboardButton("👑 Снять админа", callback_data="admin_remove_admin")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton("📨 Сообщения поддержки", callback_data="admin_support_messages")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="close_admin")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")]])
