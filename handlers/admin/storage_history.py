import datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import domain.product
import product_storage
import users
from auxiliary.system_functions import TEXT_PARSERS
from handlers.admin import AdminStates, get_initial_keyboard, get_initial_message
from handlers.roles import IsAdmin
from pkg import dp, get_keyboard, get_now_date, log_function_name
from users import get_user_by_id


@dp.message_handler(IsAdmin(),
                    lambda message: message.text=='storage_history',
                    state=AdminStates.INITIAL_STATE)
async def storage_history(message: types.Message):
    """Выбрать статистику по изменениям в продуктах"""
    await StorageHistoryStates.WAITING_CHOOSE_ACTION.set()
    keyboard = get_keyboard(STORAGE_HISTORY_ACTIONS + STORAGE_HISTORY_AUXILIARY_ACTIONS)
    await message.answer("Выберите действие", reply_markup=keyboard)


class StorageHistoryStates(StatesGroup):
    WAITING_CHOOSE_ACTION = State()
    WAITING_CHOOSE_RESTRICTIONS = State()
    WAITING_CHOOSE_RESTRICTION_WORKER = State()


@dp.message_handler(IsAdmin(),
                    lambda message: message.text in [STORAGE_HISTORY_ACTIONS[1]] + STORAGE_HISTORY_AUXILIARY_ACTIONS,
                    state=StorageHistoryStates.WAITING_CHOOSE_ACTION)
async def storage_history_add_restriction(message: types.Message):
    """Выбрать статистику по изменениям в продуктах"""
    action = message.text
    if action == STORAGE_HISTORY_AUXILIARY_ACTIONS[0]:
        return await get_initial_message(message)

    await StorageHistoryStates.WAITING_CHOOSE_RESTRICTIONS.set()
    keyboard = get_keyboard(STORAGE_HISTORY_RESTRICTIONS + STORAGE_HISTORY_AUXILIARY_ACTIONS)
    await message.answer("Выберите ограничение", reply_markup=keyboard)


@dp.message_handler(IsAdmin(),
                    lambda message: message.text in STORAGE_HISTORY_RESTRICTIONS[0:1] + STORAGE_HISTORY_AUXILIARY_ACTIONS,
                    state=StorageHistoryStates.WAITING_CHOOSE_RESTRICTIONS)
async def storage_history_add_restriction_worker(message: types.Message):
    """Отправляет статистику трат"""
    action = message.text
    if action == STORAGE_HISTORY_AUXILIARY_ACTIONS[0]:
        return await get_initial_message(message)

    await StorageHistoryStates.WAITING_CHOOSE_RESTRICTION_WORKER.set()
    workers = users.get_users()
    names = [worker.name for worker in workers]
    keyboard = get_keyboard(names + STORAGE_HISTORY_AUXILIARY_ACTIONS)
    await message.answer("Выберите цель", reply_markup=keyboard)


@dp.message_handler(IsAdmin(),
                    state=StorageHistoryStates.WAITING_CHOOSE_RESTRICTION_WORKER)
async def storage_history_add_restriction_worker_name(message: types.Message, state: FSMContext):
    """Отправляет статистику трат"""
    action = message.text
    if action == STORAGE_HISTORY_AUXILIARY_ACTIONS[0]:
        return await get_initial_message(message)

    name = action
    workers = users.get_users()
    names = [worker.name for worker in workers]

    if name not in names:
        return await storage_history_add_restriction_worker(message)
    await state.update_data({STORAGE_HISTORY_DATA[0]: name})
    await message.answer(f"Добавлено ограничение по имени: {name}")
    await storage_history(message)


@dp.message_handler(IsAdmin(),
                    lambda message: message.text==STORAGE_HISTORY_RESTRICTIONS[2],
                    state=StorageHistoryStates.WAITING_CHOOSE_RESTRICTIONS)
async def storage_history_add_restriction_product(message: types.Message, state=FSMContext):
    """Отправляет статистику трат"""
    action = message.text
    if action == STORAGE_HISTORY_AUXILIARY_ACTIONS[0]:
        return await get_initial_message(message)

    name = action
    workers = users.get_users()
    names = [worker.name for worker in workers]

    if name not in names:
        return await storage_history_add_restriction_worker(message)
    await state.update_data({STORAGE_HISTORY_DATA[1]: name})
    await message.answer(f"Добавлено ограничение по имени: {name}")
    await storage_history(message)


STORAGE_HISTORY_ACTIONS = ["Показать", "Добавить условие поиска", "Убрать условие поиска"]
STORAGE_HISTORY_RESTRICTIONS = ["По работнику", "По датам", "По продукту"]
STORAGE_HISTORY_AUXILIARY_ACTIONS = ["Вернуться назад"]
STORAGE_HISTORY_DATA = ["restriction_worker_name", "product", "products_category"]


class SetPriceStates(StatesGroup):
    WAITING_PRODUCT_NAME = State()
    WAITING_PRODUCT_NAME_2 = State()
    WAITING_NEW_PRICE = State()
