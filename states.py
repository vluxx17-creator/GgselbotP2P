from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_complete_deal = State()
    waiting_for_balance_amount = State()
    waiting_for_admin_user_id = State()
    waiting_for_support_reply = State()
