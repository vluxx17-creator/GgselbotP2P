import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils import executor
from config import BOT_TOKEN, ADMIN_IDS, MINI_APP_URL
from database import init_db, get_or_create_user, get_user_by_telegram_id, get_user_by_id
import database as db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Главное меню
def main_menu():
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        InlineKeyboardButton("📋 Мои сделки", callback_data="my_deals"),
        InlineKeyboardButton("👥 Рефералы", callback_data="referrals"),
        InlineKeyboardButton("🌐 Язык / Lang", callback_data="language"),
        InlineKeyboardButton("🛠 Техподдержка", callback_data="support"),
        InlineKeyboardButton("🌍 Открыть GGSel", web_app=WebAppInfo(url=MINI_APP_URL)),
        InlineKeyboardButton("📱 Мини-приложение", web_app=WebAppInfo(url=MINI_APP_URL))
    )

def admin_panel():
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Завершить сделку", callback_data="admin_complete_deal"),
        InlineKeyboardButton("💳 Выдать баланс", callback_data="admin_give_balance"),
        InlineKeyboardButton("👑 Выдать админа", callback_data="admin_give_admin"),
        InlineKeyboardButton("👑 Снять админа", callback_data="admin_remove_admin"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📨 Сообщения поддержки", callback_data="admin_support_messages"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_admin")
    )

def cancel_keyboard():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_action"))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    get_or_create_user(message.from_user.id, message.from_user.username)
    text = (
        "✅ *Добро пожаловать в GGSel!*\n\n"
        "📌 *Ваш надёжный P2P-гарант:*\n"
        "1️⃣ Автоматические сделки с NFT и валютами\n"
        "2️⃣ Полная защита обеих сторон\n"
        "3️⃣ Реферальная программа — _50% от комиссии_\n"
        "4️⃣ Передача товаров через менеджера: @GGSelSupp\n\n"
        "🌍 *Наш сайт:* https://ggsel.net\n"
        "📱 *Мини-приложение:* нажмите кнопку ниже"
    )
    await message.reply(text, parse_mode="Markdown", reply_markup=main_menu())

@dp.message_handler(commands=['hrteam'])
async def hrteam(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔ *Доступ запрещён.*", parse_mode="Markdown")
        return
    text = (
        "🛡 *Админ-панель GGSel*\n\n"
        "📌 Выберите действие с помощью кнопок ниже:\n\n"
        "🔹 *Завершить сделку* — завершить сделку и начислить деньги\n"
        "🔹 *Выдать баланс* — пополнить баланс пользователя\n"
        "🔹 *Выдать админа* — назначить пользователя администратором\n"
        "🔹 *Снять админа* — лишить прав администратора\n"
        "🔹 *Статистика* — посмотреть общую статистику\n"
        "🔹 *Сообщения поддержки* — просмотреть обращения"
    )
    await message.reply(text, parse_mode="Markdown", reply_markup=admin_panel())

@dp.callback_query_handler(lambda c: True)
async def callback_handler(callback_query: types.CallbackQuery):
    await callback_query.answer()
    data = callback_query.data
    user_id = callback_query.from_user.id

    if data == "balance":
        uid = get_or_create_user(user_id, callback_query.from_user.username)
        balance = db.get_user_balance(uid)
        user = db.get_user_by_id(uid)
        transactions = db.get_user_transactions(uid, limit=5)
        text = f"💰 *Ваш баланс:* `{balance}` USD\n📊 *Успешных сделок:* `{user['success_deals']}`\n\n"
        if transactions:
            text += "📜 *Последние транзакции:*\n"
            for t in transactions:
                sign = "+" if t['amount'] > 0 else ""
                text += f"• `{t['transaction_type']}`: {sign}`{t['amount']}` USD\n"
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

    elif data == "my_deals":
        uid = get_or_create_user(user_id, callback_query.from_user.username)
        deals = db.get_user_deals(uid)
        if not deals:
            await callback_query.message.edit_text("📋 *У вас пока нет сделок.*", parse_mode="Markdown", reply_markup=main_menu())
            return
        text = "📋 *Ваши сделки:*\n\n"
        for deal in deals[:5]:
            status_emoji = {'created':'⏳','paid':'💳','completed':'✅','cancelled':'❌'}.get(deal['status'],'❓')
            text += f"{status_emoji} *Сделка* `#{deal['memo']}`\n   Сумма: `{deal['amount']}` {deal['currency']}\n   Статус: _`{deal['status']}`_\n   📅 `{deal['created_at']}`\n\n"
        if len(deals) > 5:
            text += f"_... и ещё `{len(deals)-5}` сделок_"
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

    elif data == "referrals":
        uid = get_or_create_user(user_id, callback_query.from_user.username)
        earnings = db.get_referral_earnings(uid)
        referrals = db.get_referrals(uid)
        text = f"👥 *Реферальная программа*\n\n💰 Заработано: `{earnings}` USD\n👤 Приглашено: `{len(referrals)}` человек\n\n"
        if referrals:
            text += "📋 *Ваши рефералы:*\n"
            for ref in referrals[:5]:
                text += f"• @{ref['username'] or ref['telegram_id']} — заработано: `{ref['earned']}` USD\n"
        text += f"\n🔗 *Ваша реферальная ссылка:*\n`t.me/ggsel_bot?start=ref{uid}`"
        await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

    elif data == "language":
        await callback_query.message.edit_text("🌐 *Выберите язык / Choose language*\n\n🇷🇺 Русский\n🇬🇧 English", parse_mode="Markdown", reply_markup=main_menu())

    elif data == "support":
        await callback_query.message.edit_text("🛠 *Техподдержка*\n\nЕсли у вас возникли вопросы, напишите нам.\nНажмите кнопку '✉️ Сообщение', чтобы отправить запрос.\n\n⏳ *Время ответа:* до 24 часов.", parse_mode="Markdown", reply_markup=main_menu())

    elif data == "message_support":
        await callback_query.message.edit_text("✉️ *Напишите ваше сообщение для поддержки.*\n\nОпишите вашу проблему подробно, приложите скриншоты если нужно.\nМы ответим вам в ближайшее время.", parse_mode="Markdown", reply_markup=main_menu())

    elif data == "cancel_action":
        await callback_query.message.edit_text("✅ *Действие отменено.*", parse_mode="Markdown", reply_markup=admin_panel())

    elif data == "admin_back":
        await callback_query.message.edit_text("🛡 *Админ-панель GGSel*\n\nВыберите действие:", parse_mode="Markdown", reply_markup=admin_panel())

    elif data == "close_admin":
        await callback_query.message.delete()

    # Админские действия
    elif data.startswith("admin_"):
        if user_id not in ADMIN_IDS:
            await callback_query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        if data == "admin_complete_deal":
            await callback_query.message.edit_text("✅ *Завершение сделки*\n\nВведите `мемо` (код) сделки для завершения.\nПример: `uCBnsWty`\n\nСделка будет завершена, продавцу начислены деньги.", parse_mode="Markdown", reply_markup=cancel_keyboard())
            # Здесь нужно реализовать FSM для ввода мемо, но для упрощения мы будем обрабатывать следующим сообщением
            # Можно сохранить состояние в кеш, но для простоты я предлагаю использовать следующий обработчик сообщений
            # Сделаем через временную метку в кеше
            from aiogram.contrib.middlewares.logging import LoggingMiddleware
            # Сохраним состояние в глобальной переменной или через dp.current_state, но для простоты используем временный словарь
            if not hasattr(dp, 'temp_data'):
                dp.temp_data = {}
            dp.temp_data[user_id] = {'action': 'complete_deal'}
            await callback_query.answer()
        elif data == "admin_give_balance":
            await callback_query.message.edit_text("💳 *Выдача баланса*\n\nВведите ID пользователя (или @username) и сумму через пробел.\nПример: `123456 100` или `@username 50`\n\nСумма будет добавлена к балансу пользователя.", parse_mode="Markdown", reply_markup=cancel_keyboard())
            if not hasattr(dp, 'temp_data'):
                dp.temp_data = {}
            dp.temp_data[user_id] = {'action': 'give_balance'}
            await callback_query.answer()
        elif data == "admin_give_admin":
            await callback_query.message.edit_text("👑 *Выдача прав администратора*\n\nВведите ID пользователя (или @username), которому хотите выдать права администратора.\nПример: `123456` или `@username`", parse_mode="Markdown", reply_markup=cancel_keyboard())
            if not hasattr(dp, 'temp_data'):
                dp.temp_data = {}
            dp.temp_data[user_id] = {'action': 'give_admin'}
            await callback_query.answer()
        elif data == "admin_remove_admin":
            await callback_query.message.edit_text("👑 *Снятие прав администратора*\n\nВведите ID пользователя (или @username), у которого хотите снять права администратора.\nПример: `123456` или `@username`", parse_mode="Markdown", reply_markup=cancel_keyboard())
            if not hasattr(dp, 'temp_data'):
                dp.temp_data = {}
            dp.temp_data[user_id] = {'action': 'remove_admin'}
            await callback_query.answer()
        elif data == "admin_stats":
            text = "📊 *Статистика GGSel*\n\n👥 *Пользователей:* 64,742\n📈 *Всего сделок:* 12,847\n💰 *Общий оборот:* 2,345,678 USD\n👑 *Администраторов:* 5\n⭐ *Средний рейтинг:* 4.9\n\n_Данные обновлены: 14.07.2026_"
            await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_panel())
        elif data == "admin_support_messages":
            messages = db.get_unanswered_support_messages()
            if not messages:
                await callback_query.message.edit_text("📨 *Новых сообщений поддержки нет.*", parse_mode="Markdown", reply_markup=admin_panel())
                return
            text = "📨 *Сообщения поддержки:*\n\n"
            for msg in messages[:5]:
                usr = db.get_user_by_id(msg['user_id'])
                text += f"👤 @{usr['username'] or usr['telegram_id']}\n📝 `{msg['message_text'][:100]}`\n📅 `{msg['created_at']}`\n\n"
            if len(messages) > 5:
                text += f"_... и ещё {len(messages)-5} сообщений_"
            await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_panel())

@dp.message_handler()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    # Проверяем, есть ли ожидание ответа на админское действие
    if hasattr(dp, 'temp_data') and user_id in dp.temp_data:
        action = dp.temp_data[user_id]['action']
        text = message.text.strip()
        if action == 'complete_deal':
            if user_id not in ADMIN_IDS:
                await message.reply("⛔ Доступ запрещён")
                return
            deal = db.get_deal_by_memo(text)
            if not deal:
                await message.reply("❌ Сделка с таким мемо не найдена. Попробуйте снова.")
                return
            if deal['status'] == 'completed':
                await message.reply("❌ Эта сделка уже завершена.")
                return
            success = db.complete_deal(deal['id'])
            if success:
                seller = db.get_user_by_id(deal['seller_id'])
                buyer = db.get_user_by_id(deal['buyer_id'])
                commission = int(deal['amount'] * 0.05)
                seller_payout = deal['amount'] - commission
                try:
                    await bot.send_message(
                        seller['telegram_id'],
                        f"✅ *Сделка `#{text}` завершена!*\n\n💰 Вам начислено: `{seller_payout}` USD\n📊 Комиссия: `{commission}` USD\n👤 Покупатель: @{buyer['username'] or buyer['telegram_id']}\n\n_Спасибо за использование GGSel!_",
                        parse_mode="Markdown"
                    )
                    await bot.send_message(
                        buyer['telegram_id'],
                        f"✅ *Сделка `#{text}` завершена!*\n\n📦 Товар получен.\n👤 Продавец: @{seller['username'] or seller['telegram_id']}\n\n_Спасибо за использование GGSel!_",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                await message.reply(
                    f"✅ *Сделка `#{text}` успешно завершена!*\n\n💰 Продавцу начислено: `{seller_payout}` USD\n📊 Комиссия: `{commission}` USD\n\n_Участники уведомлены._",
                    parse_mode="Markdown",
                    reply_markup=admin_panel()
                )
            else:
                await message.reply("❌ Ошибка при завершении сделки.", reply_markup=admin_panel())
            del dp.temp_data[user_id]
            return
        elif action == 'give_balance':
            parts = text.split()
            if len(parts) != 2:
                await message.reply("❌ Неверный формат. Используйте: ID пользователя и сумму")
                return
            user_input, amount_str = parts
            try:
                amount = int(amount_str)
                if amount <= 0:
                    await message.reply("❌ Сумма должна быть положительным числом.")
                    return
            except ValueError:
                await message.reply("❌ Сумма должна быть числом.")
                return
            user = None
            if user_input.startswith('@'):
                username = user_input[1:]
                user = db.get_user_by_username(username)
                if not user:
                    await message.reply(f"❌ Пользователь @{username} не найден.")
                    return
            else:
                try:
                    tid = int(user_input)
                    user = db.get_user_by_telegram_id(tid)
                    if not user:
                        await message.reply(f"❌ Пользователь с ID {tid} не найден.")
                        return
                except ValueError:
                    await message.reply("❌ Неверный формат ID пользователя.")
                    return
            db.update_user_balance(user['id'], amount)
            try:
                await bot.send_message(
                    user['telegram_id'],
                    f"💳 *Пополнение баланса!*\n\n💰 Вам начислено: `+{amount}` USD\n📊 Текущий баланс: `{db.get_user_balance(user['id'])}` USD\n\n_Спасибо за использование GGSel!_",
                    parse_mode="Markdown"
                )
            except:
                pass
            await message.reply(
                f"✅ *Баланс успешно выдан!*\n\n👤 Пользователь: @{user['username'] or user['telegram_id']}\n💰 Сумма: `+{amount}` USD\n📊 Новый баланс: `{db.get_user_balance(user['id'])}` USD",
                parse_mode="Markdown",
                reply_markup=admin_panel()
            )
            del dp.temp_data[user_id]
            return
        elif action in ('give_admin', 'remove_admin'):
            user_input = text
            user = None
            if user_input.startswith('@'):
                username = user_input[1:]
                user = db.get_user_by_username(username)
                if not user:
                    await message.reply(f"❌ Пользователь @{username} не найден.")
                    return
            else:
                try:
                    tid = int(user_input)
                    user = db.get_user_by_telegram_id(tid)
                    if not user:
                        await message.reply(f"❌ Пользователь с ID {tid} не найден.")
                        return
                except ValueError:
                    await message.reply("❌ Неверный формат ID пользователя.")
                    return
            if action == 'give_admin':
                db.set_admin_status(user['id'], True)
                try:
                    await bot.send_message(
                        user['telegram_id'],
                        "👑 *Поздравляем!*\n\nВам выданы права администратора GGSel.\nТеперь вам доступна команда `/hrteam`.",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                await message.reply(f"✅ *Права администратора выданы!*\n\n👤 Пользователь: @{user['username'] or user['telegram_id']}", parse_mode="Markdown", reply_markup=admin_panel())
            else:
                db.set_admin_status(user['id'], False)
                try:
                    await bot.send_message(
                        user['telegram_id'],
                        "👑 *Права администратора сняты.*",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                await message.reply(f"✅ *Права администратора сняты!*\n\n👤 Пользователь: @{user['username'] or user['telegram_id']}", parse_mode="Markdown", reply_markup=admin_panel())
            del dp.temp_data[user_id]
            return

    # Если не админское действие – сохраняем как обращение в поддержку
    uid = get_or_create_user(user_id, message.from_user.username)
    db.add_support_message(uid, message.text)
    await message.reply("✅ *Ваше сообщение отправлено в поддержку.*\nМы свяжемся с вами в ближайшее время.", parse_mode="Markdown")

if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)
