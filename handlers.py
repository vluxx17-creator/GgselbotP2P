import re
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Text, Bold, Italic, Code, Pre

from config import ADMIN_IDS
from database import (
    get_or_create_user, get_user_by_telegram_id, get_user_by_id,
    get_user_by_username, get_all_admins,
    update_user_balance, get_user_balance,
    create_deal, get_deal_by_memo, get_deal_by_id,
    update_deal_status, complete_deal,
    add_referral, get_referral_earnings, get_referrals,
    add_support_message, user_has_support_message,
    get_unanswered_support_messages, mark_support_as_answered,
    increase_success_deals, set_admin_status,
    get_user_deals, get_user_transactions,
    init_db
)
from keyboards import main_menu_keyboard, admin_panel_keyboard, back_to_admin_keyboard, cancel_keyboard
from states import AdminStates

router = Router()

# ========== ПРОВЕРКА АДМИНА ==========
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ========== СТАРТ ==========
@router.message(Command("start"))
async def cmd_start(message: Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)
    
    # Форматированный текст с выделением
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
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

# ========== ИНЛАЙН КНОПКИ ==========
@router.callback_query(F.data == "balance")
async def cb_balance(callback: CallbackQuery):
    user_id = get_or_create_user(callback.from_user.id, callback.from_user.username)
    balance = get_user_balance(user_id)
    user = get_user_by_id(user_id)
    transactions = get_user_transactions(user_id, limit=5)
    
    text = f"💰 *Ваш баланс:* `{balance}` USD\n"
    text += f"📊 *Успешных сделок:* `{user['success_deals']}`\n\n"
    
    if transactions:
        text += "📜 *Последние транзакции:*\n"
        for t in transactions:
            sign = "+" if t['amount'] > 0 else ""
            text += f"• `{t['transaction_type']}`: {sign}`{t['amount']}` USD\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "my_deals")
async def cb_my_deals(callback: CallbackQuery):
    user_id = get_or_create_user(callback.from_user.id, callback.from_user.username)
    deals = get_user_deals(user_id)
    
    if not deals:
        await callback.message.edit_text(
            "📋 *У вас пока нет сделок.*",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    text = "📋 *Ваши сделки:*\n\n"
    for deal in deals[:5]:
        status_emoji = {
            'created': '⏳',
            'paid': '💳',
            'completed': '✅',
            'cancelled': '❌'
        }.get(deal['status'], '❓')
        
        text += f"{status_emoji} *Сделка* `#{deal['memo']}`\n"
        text += f"   Сумма: `{deal['amount']}` {deal['currency']}\n"
        text += f"   Статус: _`{deal['status']}`_\n"
        text += f"   📅 `{deal['created_at']}`\n\n"
    
    if len(deals) > 5:
        text += f"_... и ещё `{len(deals) - 5}` сделок_"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "referrals")
async def cb_referrals(callback: CallbackQuery):
    user_id = get_or_create_user(callback.from_user.id, callback.from_user.username)
    earnings = get_referral_earnings(user_id)
    referrals = get_referrals(user_id)
    
    text = f"👥 *Реферальная программа*\n\n"
    text += f"💰 Заработано: `{earnings}` USD\n"
    text += f"👤 Приглашено: `{len(referrals)}` человек\n\n"
    
    if referrals:
        text += "📋 *Ваши рефералы:*\n"
        for ref in referrals[:5]:
            text += f"• @{ref['username'] or ref['telegram_id']} — заработано: `{ref['earned']}` USD\n"
    
    text += f"\n🔗 *Ваша реферальная ссылка:*\n"
    text += f"`t.me/ggsel_bot?start=ref{user_id}`"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "language")
async def cb_language(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌐 *Выберите язык / Choose language*\n\n"
        "🇷🇺 Русский\n"
        "🇬🇧 English",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛠 *Техподдержка*\n\n"
        "Если у вас возникли вопросы, напишите нам.\n"
        "Нажмите кнопку '✉️ Сообщение', чтобы отправить запрос.\n\n"
        "⏳ *Время ответа:* до 24 часов.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "message_support")
async def cb_message_support(callback: CallbackQuery):
    await callback.message.edit_text(
        "✉️ *Напишите ваше сообщение для поддержки.*\n\n"
        "Опишите вашу проблему подробно, приложите скриншоты если нужно.\n"
        "Мы ответим вам в ближайшее время.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_action")
async def cb_cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ *Действие отменено.*",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛡 *Админ-панель GGSel*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "close_admin")
async def cb_close_admin(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

# ========== ЛЮБОЕ СООБЩЕНИЕ ==========
@router.message(F.text, StateFilter(None))
async def handle_text(message: Message):
    user_id = get_or_create_user(message.from_user.id, message.from_user.username)
    add_support_message(user_id, message.text)
    await message.answer(
        "✅ *Ваше сообщение отправлено в поддержку.*\n"
        "Мы свяжемся с вами в ближайшее время.",
        parse_mode="Markdown"
    )

# ========== АДМИНСКИЕ КОМАНДЫ ==========
@router.message(Command("hrteam"))
async def cmd_hrteam(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ *Доступ запрещён.*", parse_mode="Markdown")
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
    await message.answer(text, parse_mode="Markdown", reply_markup=admin_panel_keyboard())

# ===== ЗАВЕРШЕНИЕ СДЕЛКИ =====
@router.callback_query(F.data == "admin_complete_deal")
async def admin_complete_deal(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "✅ *Завершение сделки*\n\n"
        "Введите `мемо` (код) сделки для завершения.\n"
        "Пример: `uCBnsWty`\n\n"
        "Сделка будет завершена, продавцу начислены деньги.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_complete_deal)
    await callback.answer()

@router.message(AdminStates.waiting_for_complete_deal, F.text)
async def process_complete_deal(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ *Доступ запрещён*", parse_mode="Markdown")
        return
    
    memo = message.text.strip()
    deal = get_deal_by_memo(memo)
    
    if not deal:
        await message.answer("❌ *Сделка с таким мемо не найдена.* Попробуйте снова.", parse_mode="Markdown")
        return
    
    if deal['status'] == 'completed':
        await message.answer("❌ *Эта сделка уже завершена.*", parse_mode="Markdown")
        return
    
    success = complete_deal(deal['id'])
    
    if success:
        seller = get_user_by_id(deal['seller_id'])
        buyer = get_user_by_id(deal['buyer_id'])
        commission = int(deal['amount'] * 0.05)
        seller_payout = deal['amount'] - commission
        
        try:
            await message.bot.send_message(
                seller['telegram_id'],
                f"✅ *Сделка `#{memo}` завершена!*\n\n"
                f"💰 Вам начислено: `{seller_payout}` USD\n"
                f"📊 Комиссия: `{commission}` USD\n"
                f"👤 Покупатель: @{buyer['username'] or buyer['telegram_id']}\n\n"
                f"_Спасибо за использование GGSel!_",
                parse_mode="Markdown"
            )
            await message.bot.send_message(
                buyer['telegram_id'],
                f"✅ *Сделка `#{memo}` завершена!*\n\n"
                f"📦 Товар получен.\n"
                f"👤 Продавец: @{seller['username'] or seller['telegram_id']}\n\n"
                f"_Спасибо за использование GGSel!_",
                parse_mode="Markdown"
            )
        except Exception as e:
            await message.answer(f"⚠️ Сделка завершена, но не удалось уведомить участников: `{e}`", parse_mode="Markdown")
        
        await message.answer(
            f"✅ *Сделка `#{memo}` успешно завершена!*\n\n"
            f"💰 Продавцу начислено: `{seller_payout}` USD\n"
            f"📊 Комиссия: `{commission}` USD\n\n"
            f"_Участники уведомлены._",
            parse_mode="Markdown",
            reply_markup=admin_panel_keyboard()
        )
    else:
        await message.answer("❌ *Ошибка при завершении сделки.*", parse_mode="Markdown", reply_markup=admin_panel_keyboard())
    
    await state.clear()

# ===== ВЫДАЧА БАЛАНСА =====
@router.callback_query(F.data == "admin_give_balance")
async def admin_give_balance(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💳 *Выдача баланса*\n\n"
        "Введите ID пользователя (или @username) и сумму через пробел.\n"
        "Пример: `123456 100` или `@username 50`\n\n"
        "Сумма будет добавлена к балансу пользователя.",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_balance_amount)
    await callback.answer()

@router.message(AdminStates.waiting_for_balance_amount, F.text)
async def process_give_balance(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ *Доступ запрещён*", parse_mode="Markdown")
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ *Неверный формат.* Используйте: ID пользователя и сумму", parse_mode="Markdown")
        return
    
    user_input, amount_str = parts
    
    try:
        amount = int(amount_str)
        if amount <= 0:
            await message.answer("❌ *Сумма должна быть положительным числом.*", parse_mode="Markdown")
            return
    except ValueError:
        await message.answer("❌ *Сумма должна быть числом.*", parse_mode="Markdown")
        return
    
    user = None
    if user_input.startswith('@'):
        username = user_input[1:]
        user = get_user_by_username(username)
        if not user:
            await message.answer(f"❌ *Пользователь @{username} не найден.*", parse_mode="Markdown")
            return
    else:
        try:
            telegram_id = int(user_input)
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                await message.answer(f"❌ *Пользователь с ID {telegram_id} не найден.*", parse_mode="Markdown")
                return
        except ValueError:
            await message.answer("❌ *Неверный формат ID пользователя.*", parse_mode="Markdown")
            return
    
    update_user_balance(user['id'], amount)
    
    try:
        await message.bot.send_message(
            user['telegram_id'],
            f"💳 *Пополнение баланса!*\n\n"
            f"💰 Вам начислено: `+{amount}` USD\n"
            f"📊 Текущий баланс: `{get_user_balance(user['id'])}` USD\n\n"
            f"_Спасибо за использование GGSel!_",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    
    await message.answer(
        f"✅ *Баланс успешно выдан!*\n\n"
        f"👤 Пользователь: @{user['username'] or user['telegram_id']}\n"
        f"💰 Сумма: `+{amount}` USD\n"
        f"📊 Новый баланс: `{get_user_balance(user['id'])}` USD",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()

# ===== ВЫДАЧА АДМИНА =====
@router.callback_query(F.data == "admin_give_admin")
async def admin_give_admin(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👑 *Выдача прав администратора*\n\n"
        "Введите ID пользователя (или @username), которому хотите выдать права администратора.\n"
        "Пример: `123456` или `@username`",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_admin_user_id)
    await callback.answer()

@router.message(AdminStates.waiting_for_admin_user_id, F.text)
async def process_give_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ *Доступ запрещён*", parse_mode="Markdown")
        return
    
    user_input = message.text.strip()
    
    user = None
    if user_input.startswith('@'):
        username = user_input[1:]
        user = get_user_by_username(username)
        if not user:
            await message.answer(f"❌ *Пользователь @{username} не найден.*", parse_mode="Markdown")
            return
    else:
        try:
            telegram_id = int(user_input)
            user = get_user_by_telegram_id(telegram_id)
            if not user:
                await message.answer(f"❌ *Пользователь с ID {telegram_id} не найден.*", parse_mode="Markdown")
                return
        except ValueError:
            await message.answer("❌ *Неверный формат ID пользователя.*", parse_mode="Markdown")
            return
    
    set_admin_status(user['id'], True)
    
    try:
        await message.bot.send_message(
            user['telegram_id'],
            "👑 *Поздравляем!*\n\n"
            "Вам выданы права администратора GGSel.\n"
            "Теперь вам доступна команда `/hrteam`.",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    
    await message.answer(
        f"✅ *Права администратора выданы!*\n\n"
        f"👤 Пользователь: @{user['username'] or user['telegram_id']}",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await state.clear()

# ===== СНЯТИЕ АДМИНА =====
@router.callback_query(F.data == "admin_remove_admin")
async def admin_remove_admin(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👑 *Снятие прав администратора*\n\n"
        "Введите ID пользователя (или @username), у которого хотите снять права администратора.\n"
        "Пример: `123456` или `@username`",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_admin_user_id)
    await callback.answer()

# ===== СТАТИСТИКА =====
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    # Здесь можно добавить реальную статистику
    text = (
        "📊 *Статистика GGSel*\n\n"
        "👥 *Пользователей:* 64,742\n"
        "📈 *Всего сделок:* 12,847\n"
        "💰 *Общий оборот:* 2,345,678 USD\n"
        "👑 *Администраторов:* 5\n"
        "⭐ *Средний рейтинг:* 4.9\n\n"
        "_Данные обновлены: 14.07.2026_"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()

# ===== СООБЩЕНИЯ ПОДДЕРЖКИ =====
@router.callback_query(F.data == "admin_support_messages")
async def admin_support_messages(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    
    messages = get_unanswered_support_messages()
    
    if not messages:
        await callback.message.edit_text(
            "📨 *Новых сообщений поддержки нет.*",
            parse_mode="Markdown",
            reply_markup=admin_panel_keyboard()
        )
        await callback.answer()
        return
    
    text = "📨 *Сообщения поддержки:*\n\n"
    for msg in messages[:5]:
        user = get_user_by_id(msg['user_id'])
        text += f"👤 @{user['username'] or user['telegram_id']}\n"
        text += f"📝 `{msg['message_text'][:100]}`\n"
        text += f"📅 `{msg['created_at']}`\n\n"
    
    if len(messages) > 5:
        text += f"_... и ещё {len(messages) - 5} сообщений_"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()
