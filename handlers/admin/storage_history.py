from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import product_storage
import users
from auxiliary.system_functions import TEXT_PARSERS
from handlers.admin.handlers import get_initial_message
from handlers.admin import AdminStates, get_initial_keyboard
from handlers.roles import IsAdmin
from pkg import dp, get_keyboard
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
                    lambda message: message.text in STORAGE_HISTORY_RESTRICTIONS[1:2] + STORAGE_HISTORY_AUXILIARY_ACTIONS,
                    state=StorageHistoryStates.WAITING_CHOOSE_RESTRICTIONS)
async def storage_history_add_restriction_date(message: types.Message):
    changes = product_storage.get_product_changes()
    if not changes:
        await message.answer("Нет поступлений", reply_markup=get_initial_keyboard())
        return
    answer_string = ""
    for date in sorted(changes):
        answer_string += date
        for user_id in changes[date]:
            user = get_user_by_id(user_id)
            answer_string += f"\n{user.name}:" + product_storage.volumes_string(changes[date][user_id]) + "\n"
    await message.answer(answer_string)


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
    await state.update_data({STORAGE_HISTORY_DATA[3]: name})
    await message.answer(f"Добавлено ограничение по имени: {name}")
    await storage_history(message)


@dp.message_handler(IsAdmin(),
                    lambda message: message.text in [STORAGE_HISTORY_ACTIONS[0]],
                    state=StorageHistoryStates.WAITING_CHOOSE_ACTION)
async def storage_history_show(message: types.Message, state: FSMContext):
    """Выбрать статистику по изменениям в продуктах"""
    action = message.text
    if action == STORAGE_HISTORY_AUXILIARY_ACTIONS[0]:
        return await get_initial_message(message)

    data = await state.get_data()
    worker_name = data.get(STORAGE_HISTORY_DATA[0])
    from_date = data.get(STORAGE_HISTORY_DATA[1])
    to_date = data.get(STORAGE_HISTORY_DATA[2])
    product: product_storage.Product = data.get(STORAGE_HISTORY_DATA[3])
    product_category = data.get(STORAGE_HISTORY_DATA[4])

    if worker_name:
        worker = users.get_user_by_name(worker_name)
        user_ids = [worker.user_id]
    else:
        user_ids = None

    if product:
        product_ids = [product.id]
    else:
        product_ids = None

    changes = product_storage.get_product_changes(user_ids=user_ids,
                                                  product_ids=product_ids,
                                                  from_date=from_date,
                                                  to_date=to_date)

    if not changes:
        await message.answer("Нет поступлений", reply_markup=get_initial_keyboard())
        return
    parsing_mode = "HTML"
    bold = TEXT_PARSERS[parsing_mode]["bold"]
    result_string = ""
    result_sum = 0
    answers = []
    sorted_changes = sorted(changes)
    for date in sorted_changes:
        answer_string = ""
        answer_string += f"\n\n<b>{date}</b>"
        for user_id in changes[date]:
            user = get_user_by_id(user_id)
            #answer_string += "<i>Курсив</i> <b>жирный</b> <i><b>жирный курсив</b></i>"
            #answer_string += "*a* **b** ***c***\n"
            answer_string += f"\n<u><i>{user.name}</i></u>:" + product_storage.volumes_string(changes[date][user_id]) + "\n"
            cost_sum = product_storage.volumes_cost_sum(changes[date][user_id])
            answer_string += bold(f"{cost_sum} лари\n")
            result_sum += cost_sum
        if len(result_string + answer_string) > 4000:
            answers.append(result_string)
            result_string = answer_string
        else:
            result_string += answer_string
    result_string += bold(f"\nВсего {result_sum} лари")
    answers.append(result_string)
    for answer in answers:
        await message.answer(answer, parse_mode=parsing_mode)


STORAGE_HISTORY_ACTIONS = ["Показать", "Добавить условие поиска", "Убрать условие поиска"]
STORAGE_HISTORY_RESTRICTIONS = ["По работнику", "По датам", "По продукту"]
STORAGE_HISTORY_AUXILIARY_ACTIONS = ["Вернуться назад"]
STORAGE_HISTORY_DATA = ["restriction_worker_name", "from_date", "to_date", "product", "products_category"]


class SetPriceStates(StatesGroup):
    WAITING_PRODUCT_NAME = State()
    WAITING_PRODUCT_NAME_2 = State()
    WAITING_NEW_PRICE = State()
