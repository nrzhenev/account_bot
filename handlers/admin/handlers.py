import datetime
import logging
# import product_storage
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import actions
import categories as categories_module
import expenses
import money
import product_storage
from handlers.admin import AdminStates, get_initial_keyboard


def init_handlers():
    from handlers.admin.get_balance_history import get_actions_between_dates
    from handlers.admin.money_receive import verify_message_is_value
    from handlers.admin.money_transfer import transfer_money
    from handlers.admin.set_date_interval import choose_action
    from handlers.admin.set_price import set_price
    from handlers.admin.storage_history import storage_history_add_restriction


init_handlers()

LOGGER = logging.getLogger(__name__)


# import poster_storage as ps
from handlers.roles import IsAdmin
from pkg import (dp, get_keyboard, get_now_date, log_function_name)


class GetStatisticsStates(StatesGroup):
    WAITING_TO_CHOOSE_ACTION = State()


class UserStates(StatesGroup):
    WAITING_FOR_FIRST_RESPONSE = State()
    WAITING_FOR_SECOND_RESPONSE = State()


class ActionsStates(StatesGroup):
    WAITING_ACTION = State()


@log_function_name
@dp.message_handler(IsAdmin(), commands=['start', 'help'])
async def start(message: types.Message, state: FSMContext):
    await state.reset_state()
    await AdminStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


@dp.message_handler(lambda message: message.text == "История действий", state=AdminStates.INITIAL_STATE)
async def get_actions(message: types.Message, state: FSMContext):
    #await ActionsStates.WAITING_ACTION.set()
    data = await state.get_data()
    from_date = data.get('from_date', get_now_date() - datetime.timedelta(days=200))
    to_date = data.get('to_date', get_now_date())
    acts = actions.get_actions_between_dates(from_date, to_date)
    result = "Действия:\n"
    # for act in acts:
    #     result += str(act)
    result += actions.actions_string(acts)
    await message.answer(result)


@dp.message_handler(lambda message: message.text == "Статистика", state=AdminStates.INITIAL_STATE)
async def get_actions(message: types.Message, state: FSMContext):
    await GetStatisticsStates.WAITING_TO_CHOOSE_ACTION.set()
    kb = get_keyboard(["Траты", "Списания"])
    await message.answer("Выберите действие", reply_markup=kb)


async def _get_most_similar(message: types.Message, state: FSMContext):
    if message.text in []:
        pass
    sub_name = message.text
    product = product_storage.get_product_by_name(sub_name)
    if product:
        await ReceivingByHandStates.WAITING_SUPPLY_QUANTITY.set()
        await message.answer(f"Для {product.name} введите количество {product.measurement_unit}:")
        await state.update_data(current_product=product)
        return

    names = get_products_names_most_similar(sub_name, 5)
    keyboard = get_keyboard(names)
    keyboard.add(KeyboardButton(text="Назад"))
    await message.answer(f"Выберите из предложенных или повторите попытку", reply_markup=keyboard)


@dp.message_handler(IsAdmin(), lambda message: message.text=='balance', state=AdminStates.INITIAL_STATE)
async def balance(message: types.Message):
    await message.answer(money.balance_report())


@dp.message_handler(IsAdmin(), lambda message: message.text == "expenses", state=AdminStates.INITIAL_STATE)
async def get_expenses(message: types.Message):
    exp = expenses.get_month_expenses()
    if not exp:
        await message.answer("Нет трат")
    await message.answer(expenses.expenses_string(exp), parse_mode="HTML")


@dp.message_handler(IsAdmin(), state=UserStates.WAITING_FOR_FIRST_RESPONSE)
async def restructure_other2(message: types.Message, state: FSMContext):
    alias = message.text
    await state.update_data(first_response=alias)
    similar_aliases = categories_module.get_aliases_most_similar(alias, 5)
    similar_products = [categories_module.get_product_by_alias(al) for al in similar_aliases]
    similar_aliases_names = [product.name for product in set(similar_products)]
    keyboard = ReplyKeyboardMarkup(selective=True)
    buttons = [KeyboardButton(text=name) for name in similar_aliases_names]
    keyboard.add(*buttons)
    await message.answer(f"Выберите имя или впишите новое", reply_markup=keyboard)
    await UserStates.WAITING_FOR_SECOND_RESPONSE.set()


@dp.message_handler(IsAdmin(), state=UserStates.WAITING_FOR_SECOND_RESPONSE)
async def restructure_other3(message: types.Message, state: FSMContext):
    name = message.text
    data = await state.get_data()
    alias = data.get('first_response')
    categories_module.set_new_name_to_alias(alias, name)
    await message.answer(f"Успешно назначили имя {name} алиасу {alias}")
    await state.finish()

# @dp.message_handler(IsAdmin(), commands=['gm__'])
# async def get_messages(message: types.Message):
#     await message.answer(messages.get_messages())
#
