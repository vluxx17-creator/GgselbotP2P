import asyncio
import logging
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from config import BOT_TOKEN, ADMIN_IDS, MINI_APP_URL
from database import init_db, get_or_create_user, get_user_by_telegram_id, get_user_by_id
from keyboards import main_menu_keyboard, admin_panel_keyboard, cancel_keyboard
import database as db

logging.basicConfig(level=logging.INFO)

# Состояния для ConversationHandler
(WAITING_COMPLETE_DEAL, WAITING_BALANCE_AMOUNT, WAITING_ADMIN_USER_ID) = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
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
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "balance":
        user_id = get_or_create_user(query.from_user.id, query.from_user.username)
        balance = db.get_user_balance(user_id)
        user = db.get_user_by_id(user_id)
        transactions = db.get_user_transactions(user_id, limit=5)
        text = f"💰 *Ваш баланс:* `{balance}` USD\n📊 *Успешных сделок:* `{user['success_deals']}`\n\n"
        if transactions:
            text += "📜 *Последние транзакции:*\n"
            for t in transactions:
                sign = "+" if t['amount'] > 0 else ""
                text += f"• `{t['transaction_type']}`: {sign}`{t['amount']}` USD\n"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif data == "my_deals":
        user_id = get_or_create_user(query.from_user.id, query.from_user.username)
        deals = db.get_user_deals(user_id)
        if not deals:
            await query.edit_message_text("📋 *У вас пока нет сделок.*", parse_mode='Markdown', reply_markup=main_menu_keyboard())
            return
        text = "📋 *Ваши сделки:*\n\n"
        for deal in deals[:5]:
            status_emoji = {'created':'⏳','paid':'💳','completed':'✅','cancelled':'❌'}.get(deal['status'],'❓')
            text += f"{status_emoji} *Сделка* `#{deal['memo']}`\n   Сумма: `{deal['amount']}` {deal['currency']}\n   Статус: _`{deal['status']}`_\n   📅 `{deal['created_at']}`\n\n"
        if len(deals) > 5:
            text += f"_... и ещё `{len(deals)-5}` сделок_"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif data == "referrals":
        user_id = get_or_create_user(query.from_user.id, query.from_user.username)
        earnings = db.get_referral_earnings(user_id)
        referrals = db.get_referrals(user_id)
        text = f"👥 *Реферальная программа*\n\n💰 Заработано: `{earnings}` USD\n👤 Приглашено: `{len(referrals)}` человек\n\n"
        if referrals:
            text += "📋 *Ваши рефералы:*\n"
            for ref in referrals[:5]:
                text += f"• @{ref['username'] or ref['telegram_id']} — заработано: `{ref['earned']}` USD\n"
        text += f"\n🔗 *Ваша реферальная ссылка:*\n`t.me/ggsel_bot?start=ref{user_id}`"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif data == "language":
        await query.edit_message_text("🌐 *Выберите язык / Choose language*\n\n🇷🇺 Русский\n🇬🇧 English", parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif data == "support":
        await query.edit_message_text("🛠 *Техподдержка*\n\nЕсли у вас возникли вопросы, напишите нам.\nНажмите кнопку '✉️ Сообщение', чтобы отправить запрос.\n\n⏳ *Время ответа:* до 24 часов.", parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif data == "message_support":
        await query.edit_message_text("✉️ *Напишите ваше сообщение для поддержки.*\n\nОпишите вашу проблему подробно, приложите скриншоты если нужно.\nМы ответим вам в ближайшее время.", parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif data == "cancel_action":
        context.user_data.clear()
        await query.edit_message_text("✅ *Действие отменено.*", parse_mode='Markdown', reply_markup=admin_panel_keyboard())

    elif data == "admin_back":
        context.user_data.clear()
        await query.edit_message_text("🛡 *Админ-панель GGSel*\n\nВыберите действие:", parse_mode='Markdown', reply_markup=admin_panel_keyboard())

    elif data == "close_admin":
        await query.delete_message()

    # ----- Админские -----
    elif data == "admin_complete_deal":
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        await query.edit_message_text("✅ *Завершение сделки*\n\nВведите `мемо` (код) сделки для завершения.\nПример: `uCBnsWty`\n\nСделка будет завершена, продавцу начислены деньги.", parse_mode='Markdown', reply_markup=cancel_keyboard())
        context.user_data['admin_action'] = 'complete_deal'
        return WAITING_COMPLETE_DEAL

    elif data == "admin_give_balance":
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        await query.edit_message_text("💳 *Выдача баланса*\n\nВведите ID пользователя (или @username) и сумму через пробел.\nПример: `123456 100` или `@username 50`\n\nСумма будет добавлена к балансу пользователя.", parse_mode='Markdown', reply_markup=cancel_keyboard())
        context.user_data['admin_action'] = 'give_balance'
        return WAITING_BALANCE_AMOUNT

    elif data == "admin_give_admin":
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        await query.edit_message_text("👑 *Выдача прав администратора*\n\nВведите ID пользователя (или @username), которому хотите выдать права администратора.\nПример: `123456` или `@username`", parse_mode='Markdown', reply_markup=cancel_keyboard())
        context.user_data['admin_action'] = 'give_admin'
        return WAITING_ADMIN_USER_ID

    elif data == "admin_remove_admin":
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        await query.edit_message_text("👑 *Снятие прав администратора*\n\nВведите ID пользователя (или @username), у которого хотите снять права администратора.\nПример: `123456` или `@username`", parse_mode='Markdown', reply_markup=cancel_keyboard())
        context.user_data['admin_action'] = 'remove_admin'
        return WAITING_ADMIN_USER_ID

    elif data == "admin_stats":
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        text = "📊 *Статистика GGSel*\n\n👥 *Пользователей:* 64,742\n📈 *Всего сделок:* 12,847\n💰 *Общий оборот:* 2,345,678 USD\n👑 *Администраторов:* 5\n⭐ *Средний рейтинг:* 4.9\n\n_Данные обновлены: 14.07.2026_"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel_keyboard())

    elif data == "admin_support_messages":
        if query.from_user.id not in ADMIN_IDS:
            await query.answer("⛔ Доступ запрещён", show_alert=True)
            return
        messages = db.get_unanswered_support_messages()
        if not messages:
            await query.edit_message_text("📨 *Новых сообщений поддержки нет.*", parse_mode='Markdown', reply_markup=admin_panel_keyboard())
            return
        text = "📨 *Сообщения поддержки:*\n\n"
        for msg in messages[:5]:
            user = db.get_user_by_id(msg['user_id'])
            text += f"👤 @{user['username'] or user['telegram_id']}\n📝 `{msg['message_text'][:100]}`\n📅 `{msg['created_at']}`\n\n"
        if len(messages) > 5:
            text += f"_... и ещё {len(messages)-5} сообщений_"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel_keyboard())

    return ConversationHandler.END

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если это ответ на админское действие
    if context.user_data.get('admin_action'):
        action = context.user_data['admin_action']
        text = update.message.text.strip()
        user_id = update.effective_user.id

        if action == 'complete_deal':
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("⛔ Доступ запрещён")
                return
            deal = db.get_deal_by_memo(text)
            if not deal:
                await update.message.reply_text("❌ Сделка с таким мемо не найдена. Попробуйте снова.")
                return
            if deal['status'] == 'completed':
                await update.message.reply_text("❌ Эта сделка уже завершена.")
                return
            success = db.complete_deal(deal['id'])
            if success:
                seller = db.get_user_by_id(deal['seller_id'])
                buyer = db.get_user_by_id(deal['buyer_id'])
                commission = int(deal['amount'] * 0.05)
                seller_payout = deal['amount'] - commission
                try:
                    await update.message.bot.send_message(
                        seller['telegram_id'],
                        f"✅ *Сделка `#{text}` завершена!*\n\n💰 Вам начислено: `{seller_payout}` USD\n📊 Комиссия: `{commission}` USD\n👤 Покупатель: @{buyer['username'] or buyer['telegram_id']}\n\n_Спасибо за использование GGSel!_",
                        parse_mode='Markdown'
                    )
                    await update.message.bot.send_message(
                        buyer['telegram_id'],
                        f"✅ *Сделка `#{text}` завершена!*\n\n📦 Товар получен.\n👤 Продавец: @{seller['username'] or seller['telegram_id']}\n\n_Спасибо за использование GGSel!_",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Сделка завершена, но не удалось уведомить участников: `{e}`", parse_mode='Markdown')
                await update.message.reply_text(f"✅ *Сделка `#{text}` успешно завершена!*\n\n💰 Продавцу начислено: `{seller_payout}` USD\n📊 Комиссия: `{commission}` USD\n\n_Участники уведомлены._", parse_mode='Markdown', reply_markup=admin_panel_keyboard())
            else:
                await update.message.reply_text("❌ Ошибка при завершении сделки.", reply_markup=admin_panel_keyboard())
            context.user_data.clear()
            return

        elif action == 'give_balance':
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("⛔ Доступ запрещён")
                return
            parts = text.split()
            if len(parts) != 2:
                await update.message.reply_text("❌ Неверный формат. Используйте: ID пользователя и сумму")
                return
            user_input, amount_str = parts
            try:
                amount = int(amount_str)
                if amount <= 0:
                    await update.message.reply_text("❌ Сумма должна быть положительным числом.")
                    return
            except ValueError:
                await update.message.reply_text("❌ Сумма должна быть числом.")
                return
            user = None
            if user_input.startswith('@'):
                username = user_input[1:]
                user = db.get_user_by_username(username)
                if not user:
                    await update.message.reply_text(f"❌ Пользователь @{username} не найден.")
                    return
            else:
                try:
                    telegram_id = int(user_input)
                    user = db.get_user_by_telegram_id(telegram_id)
                    if not user:
                        await update.message.reply_text(f"❌ Пользователь с ID {telegram_id} не найден.")
                        return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат ID пользователя.")
                    return
            db.update_user_balance(user['id'], amount)
            try:
                await update.message.bot.send_message(
                    user['telegram_id'],
                    f"💳 *Пополнение баланса!*\n\n💰 Вам начислено: `+{amount}` USD\n📊 Текущий баланс: `{db.get_user_balance(user['id'])}` USD\n\n_Спасибо за использование GGSel!_",
                    parse_mode='Markdown'
                )
            except:
                pass
            await update.message.reply_text(
                f"✅ *Баланс успешно выдан!*\n\n👤 Пользователь: @{user['username'] or user['telegram_id']}\n💰 Сумма: `+{amount}` USD\n📊 Новый баланс: `{db.get_user_balance(user['id'])}` USD",
                parse_mode='Markdown',
                reply_markup=admin_panel_keyboard()
            )
            context.user_data.clear()
            return

        elif action in ('give_admin', 'remove_admin'):
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("⛔ Доступ запрещён")
                return
            user_input = text.strip()
            user = None
            if user_input.startswith('@'):
                username = user_input[1:]
                user = db.get_user_by_username(username)
                if not user:
                    await update.message.reply_text(f"❌ Пользователь @{username} не найден.")
                    return
            else:
                try:
                    telegram_id = int(user_input)
                    user = db.get_user_by_telegram_id(telegram_id)
                    if not user:
                        await update.message.reply_text(f"❌ Пользователь с ID {telegram_id} не найден.")
                        return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат ID пользователя.")
                    return
            if action == 'give_admin':
                db.set_admin_status(user['id'], True)
                try:
                    await update.message.bot.send_message(
                        user['telegram_id'],
                        "👑 *Поздравляем!*\n\nВам выданы права администратора GGSel.\nТеперь вам доступна команда `/hrteam`.",
                        parse_mode='Markdown'
                    )
                except:
                    pass
                await update.message.reply_text(f"✅ *Права администратора выданы!*\n\n👤 Пользователь: @{user['username'] or user['telegram_id']}", parse_mode='Markdown', reply_markup=admin_panel_keyboard())
            else:  # remove_admin
                db.set_admin_status(user['id'], False)
                try:
                    await update.message.bot.send_message(
                        user['telegram_id'],
                        "👑 *Права администратора сняты.*",
                        parse_mode='Markdown'
                    )
                except:
                    pass
                await update.message.reply_text(f"✅ *Права администратора сняты!*\n\n👤 Пользователь: @{user['username'] or user['telegram_id']}", parse_mode='Markdown', reply_markup=admin_panel_keyboard())
            context.user_data.clear()
            return

    # Обычное сообщение (поддержка)
    user_id = get_or_create_user(update.effective_user.id, update.effective_user.username)
    db.add_support_message(user_id, update.message.text)
    await update.message.reply_text("✅ *Ваше сообщение отправлено в поддержку.*\nМы свяжемся с вами в ближайшее время.", parse_mode='Markdown')

async def hrteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ *Доступ запрещён.*", parse_mode='Markdown')
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
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=admin_panel_keyboard())

def main():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hrteam", hrteam))

    # Обработчик callback'ов (с состояниями)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(callback_handler, pattern='^(admin_complete_deal|admin_give_balance|admin_give_admin|admin_remove_admin)$')],
        states={
            WAITING_COMPLETE_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handler)],
            WAITING_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handler)],
            WAITING_ADMIN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback_handler)],
        },
        fallbacks=[CallbackQueryHandler(callback_handler, pattern='^(cancel_action|admin_back|close_admin|admin_stats|admin_support_messages|balance|my_deals|referrals|language|support|message_support)$')],
        map_to_parent={
            WAITING_COMPLETE_DEAL: -1,
            WAITING_BALANCE_AMOUNT: -1,
            WAITING_ADMIN_USER_ID: -1,
        }
    )
    application.add_handler(conv_handler)

    # Обработчик обычных callback'ов (без состояний)
    application.add_handler(CallbackQueryHandler(callback_handler, pattern='^(balance|my_deals|referrals|language|support|message_support|cancel_action|admin_back|close_admin|admin_stats|admin_support_messages)$'))

    # Обработчик текстовых сообщений (поддержка и ответы на админские действия)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
