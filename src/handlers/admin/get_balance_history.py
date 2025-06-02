from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from src.handlers.admin import AdminStates
from src.handlers.roles import IsAdmin
from pkg import dp, get_most_similar_strings
from users import get_users
from actions import get_actions_between_dates, actions_string


def get_actions_by_user_name(user_name: str):
    usrs = get_users()
    users_by_names = {usr.name: usr for usr in usrs}
    most_similar_names = get_most_similar_strings(user_name, list(users_by_names.keys()))
    if not most_similar_names:
        return []
    user = users_by_names[most_similar_names[0]]
    acts = get_actions_between_dates()
    filtered_acts = [act for act in acts if act.user_id == user.user_id]
    return filtered_acts


@dp.message_handler(IsAdmin(), lambda message: message.text == "История денег", state=AdminStates.INITIAL_STATE)
async def products_categories(message: types.Message, state: FSMContext):
    acts = get_actions_between_dates()
    if not acts:
        await message.answer("Нету действий")
    for acts_sub in [acts[i: i+10] for i in range(0, len(acts), 10)]:
        await message.answer(f"{actions_string(acts_sub)}", parse_mode="HTML")


# @dp.message_handler(IsAdmin(), state=MoneyReceive.WAITING_RECEIVE_QUANTITY))
# async def products_categories(message: types.Message, state: FSMContext):
#     if not await verify_message_is_value(message):
#         return
#
#     initial_money = money.get_balance("Счет")
#     inc = float(re.search(MONEY_VALUE_REGEX_STRING, message.text).group())
#     money.increment("Счет", inc)
#     sum = initial_money + inc
#     await AdminStates.INITIAL_STATE.set()
#     keyboard = get_initial_keyboard()
#     await message.answer(f"Добавили {inc} на счет.\nИтого {sum}", reply_markup=keyboard)
#
#
# @dp.message_handler(IsAdmin(), lambda message: message.text == "Пополнение счета", state="*")
# async def products_categories2(message: types.Message, state: FSMContext):
#     await MoneyReceive.WAITING_RECEIVE_QUANTITY.set()
#     await message.answer("Введите сумму")


class GetBalanceHistoryStates(StatesGroup):
    WAITING_RECEPIENT_NAME = State()
    WAITING_RECEIVE_QUANTITY = State()
