import datetime
import re

# import product_storage
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import actions
from users import get_user_by_id
import categories as categories_module
import expenses
import money
import product_storage
import users
from auxiliary.system_functions import TEXT_PARSERS
# import poster_storage as ps
from handlers.roles import IsAdmin
from pkg import (dp, get_keyboard, verify_message_is_value, MONEY_VALUE_REGEX_STRING, get_now_date,
                 get_most_similar_strings)

SENDERS = ["Счет", "Никита"]


class AdminStates(StatesGroup):
    INITIAL_STATE = State()


class GetStatisticsStates(StatesGroup):
    WAITING_TO_CHOOSE_ACTION = State()


class UserStates(StatesGroup):
    WAITING_FOR_FIRST_RESPONSE = State()
    WAITING_FOR_SECOND_RESPONSE = State()


class MoneyTransfer(StatesGroup):
    WAITING_SENDER_NAME = State()
    WAITING_RECEPIENT_NAME = State()
    WAITING_TRANSFER_QUANTITY = State()


class MoneyReceive(StatesGroup):
    WAITING_RECEPIENT_NAME = State()
    WAITING_RECEIVE_QUANTITY = State()


class ActionsStates(StatesGroup):
    WAITING_ACTION = State()


@dp.message_handler(IsAdmin(), commands=['start', 'help'])
async def start(message: types.Message, state: FSMContext):
    await state.reset_state()
    await AdminStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=get_initial_keyboard())


@dp.message_handler(lambda message: message.text == "Перевести деньги", state=AdminStates.INITIAL_STATE)
async def transfer_money(message: types.Message, state: FSMContext):
    senders = SENDERS
    keyboard = get_keyboard(senders)
    text = "Откуда перевести"
    await MoneyTransfer.WAITING_SENDER_NAME.set()
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "История действий", state=AdminStates.INITIAL_STATE)
async def get_actions(message: types.Message, state: FSMContext):
    #await ActionsStates.WAITING_ACTION.set()
    acts = actions.get_actions_between_dates(get_now_date() - datetime.timedelta(days=200), get_now_date())
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


@dp.message_handler(state=MoneyTransfer.WAITING_SENDER_NAME)
async def transfer_money(message: types.Message, state: FSMContext):
    sender = message.text
    if not sender in SENDERS:
        await message.answer(f"Неправильный отправитель")
    await state.update_data(sender=sender)
    keyboard = get_keyboard(money.get_money_recepients(), True)
    text = "Выберите, кому перевести"
    await MoneyTransfer.WAITING_RECEPIENT_NAME.set()
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(state=MoneyTransfer.WAITING_RECEPIENT_NAME)
async def transfer_money_waiting_name(message: types.Message, state: FSMContext):
    recepient = message.text
    recepients = money.get_money_recepients()
    if not recepient in recepients:
        await message.answer("Неправильный получатель")
        return
    await state.update_data(recepient=recepient)
    text = "Сколько перевести"
    await MoneyTransfer.WAITING_TRANSFER_QUANTITY.set()
    await message.answer(text)


@dp.message_handler(state=MoneyTransfer.WAITING_TRANSFER_QUANTITY)
async def transfer_money_waiting_quantity(message: types.Message, state: FSMContext):
    if not await verify_message_is_value(message):
        return

    amount = re.search(MONEY_VALUE_REGEX_STRING, message.text).group()

    data = await state.get_data()
    sender = data.get("sender")
    recepient = data.get("recepient")

    money.transfer(float(amount), sender, recepient)
    text = f"Перевел {recepient} {amount} лари от {sender}"
    await AdminStates.INITIAL_STATE.set()
    await message.answer(text, reply_markup=get_initial_keyboard())


def get_initial_keyboard():
    return get_keyboard(["balance", "expenses", "set price", "Пополнение счета", "storage_history", "storage", "Перевести деньги",
                         "История действий"])


#
# @dp.message_handler(commands=['change_role'])
# async def change_role(message: types.Message):
#     markup = ReplyKeyboardMarkup(selective=True)
#     markup.add(expenses_)
#     markup.add(shipments_, other)
#
#     await message.answer('Меню', reply_markup=markup)
#
#
# @dp.message_handler(text=expenses_)
# async def process_expenses_chose_role(message: types.Message):
#     await message.answer('Вы выбрали траты')
#
#
# @dp.message_handler(text=shipments_)
# async def process_shipments_chose_role(message: types.Message):
#     await message.answer('Вы выбрали поставки')


# @dp.message_handler(text=other)
# async def process_other_chose_role(message: types.Message):
#     await message.answer('Вы выбрали другое')


@dp.message_handler(IsAdmin(), lambda message: message.text == "Пополнение счета", state="*")
async def products_categories(message: types.Message, state: FSMContext):
    await MoneyReceive.WAITING_RECEIVE_QUANTITY.set()
    await message.answer("Введите сумму")


@dp.message_handler(IsAdmin(), state=MoneyReceive.WAITING_RECEIVE_QUANTITY)
async def products_categories(message: types.Message, state: FSMContext):
    if not await verify_message_is_value(message):
        return

    initial_money = money.get_balance("Счет")
    inc = float(re.search(MONEY_VALUE_REGEX_STRING, message.text).group())
    money.increment("Счет", inc)
    sum = initial_money + inc
    await AdminStates.INITIAL_STATE.set()
    keyboard = get_initial_keyboard()
    await message.answer(f"Добавили {inc} на счет.\nИтого {sum}", reply_markup=keyboard)

#
# @dp.message_handler(commands=['today'])
# async def today_statistics(message: types.Message):
#     """Отправляет сегодняшнюю статистику трат"""
#     exp_list = expenses.get_today_expenses()
#     answer_message = expenses.print_expenses(exp_list, "сегодня")
#     await message.answer(answer_message)
#
#
# @dp.message_handler(IsAdmin(), commands=['expenses_statistics'])
# async def date_statistics(message: types.Message):
#     """Отправляет сегодняшнюю статистику трат"""
#     text = message.get_args()
#     dates = get_dates_from_string(text)
#     if not dates:
#         return
#     date = dates[0]
#     date_string = date.strftime("%d-%m-%Y")
#     exp_list = expenses.get_expenses_by_date(date_string)
#     answer_message = expenses.print_expenses(exp_list, date_string)
#     await message.answer(answer_message)


@dp.message_handler(IsAdmin(), lambda message: message.text=="storage", state=AdminStates.INITIAL_STATE)
async def storage(message: types.Message):
    """Отправляет сегодняшнюю статистику трат"""
    products = product_storage.get_products_in_storage()
    products = [product for product in products if product.quantity]
    answer_string = "Склад:"
    for product_volume in products:
        product = product_storage.get_product_by_id(product_volume.product_id)
        answer_string += "\n" + f"{product.name}: {product_volume.quantity} {product.measurement_unit}"
    await message.answer(answer_string)


# Storage History
class StorageHistoryStates(StatesGroup):
    WAITING_CHOOSE_ACTION = State()
    WAITING_CHOOSE_RESTRICTIONS = State()
    WAITING_CHOOSE_RESTRICTION_WORKER = State()


STORAGE_HISTORY_ACTIONS = ["Показать", "Добавить условие поиска", "Убрать условие поиска"]
STORAGE_HISTORY_RESTRICTIONS = ["По работнику", "По датам", "По продукту"]
STORAGE_HISTORY_AUXILIARY_ACTIONS = ["Вернуться назад"]
STORAGE_HISTORY_DATA = ["restriction_worker_name", "from_date", "to_date", "product", "products_category"]


@dp.message_handler(IsAdmin(),
                    lambda message: message.text=='storage_history',
                    state=AdminStates.INITIAL_STATE)
async def storage_history(message: types.Message):
    """Выбрать статистику по изменениям в продуктах"""
    await StorageHistoryStates.WAITING_CHOOSE_ACTION.set()
    keyboard = get_keyboard(STORAGE_HISTORY_ACTIONS + STORAGE_HISTORY_AUXILIARY_ACTIONS)
    await message.answer("Выберите действие", reply_markup=keyboard)


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
async def storage_history_add_restriction_product(message: types.Message):
    pass


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
    answer_string = ""
    result_sum = 0
    for date in sorted(changes):
        answer_string += f"\n\n<b>{date}</b>"
        for user_id in changes[date]:
            user = get_user_by_id(user_id)
            #answer_string += "<i>Курсив</i> <b>жирный</b> <i><b>жирный курсив</b></i>"
            #answer_string += "*a* **b** ***c***\n"
            answer_string += f"\n<u><i>{user.name}</i></u>:" + product_storage.volumes_string(changes[date][user_id]) + "\n"
            cost_sum = product_storage.volumes_cost_sum(changes[date][user_id])
            answer_string += bold(f"{cost_sum} лари\n")
            result_sum += cost_sum
    answer_string += bold(f"\nВсего {result_sum} лари")
    await message.answer(answer_string, parse_mode='HTML')


# @dp.message_handler(commands=['month'])
# async def month_statistics(message: types.Message):
#     """Отправляет статистику трат текущего месяца"""
#     exp_list = expenses.get_month_expenses()
#     answer_message = expenses.print_expenses(exp_list, "в этом месяце")
#     await message.answer(answer_message)

#
# @dp.message_handler(IsAdmin(), commands=['oa'])
# async def other_aliases(message: types.Message):
#     unnamed = categories_module.name_aliases_by_name()[categories_module.UNNAMED_PRODUCT_NAME]
#     result_message = unnamed.aliases
#     await message.answer(", ".join(result_message))
#
#
# @dp.message_handler(IsAdmin(), commands=['transfer'])
# async def transfer_money(message: types.Message):
#     text = message.text
#     try:
#         amount = re.search("\d+", text).group()
#         from_user = re.search("(?<=\d\s)\S+(?=\s->)", text).group()
#         to_user = re.search("(?<=->\s)\S+", text).group()
#     except Exception:
#         await message.answer("Неправильный формат. Сообщение должно быть /transfer 200 Никита -> Мириан\n"
#                              "Доступные пользователи: Мириан, Никита, Касса, Счет")
#         return
#
#     money.transfer(float(amount), from_user, to_user)
#     await message.answer(f"Успешно перевел {amount} от {from_user} к {to_user}")


# @dp.message_handler(IsAdmin(), commands=['storage'])
# async def storage(message: types.Message):
#     answer = await ps.quantity_report()
#     await message.answer(f"{answer}")


@dp.message_handler(IsAdmin(), lambda message: message.text=='balance', state=AdminStates.INITIAL_STATE)
async def balance(message: types.Message):
    await message.answer(money.balance_report())


@dp.message_handler(IsAdmin(), lambda message: message.text == "expenses", state=AdminStates.INITIAL_STATE)
async def get_expenses(message: types.Message):
    exp = expenses.get_month_expenses()
    if not exp:
        await message.answer("Нет трат")
    await message.answer(expenses.expenses_string(exp), parse_mode="HTML")


# @dp.message_handler(IsAdmin(), commands=['ro'])
# async def restructure_other(message: types.Message):
#     unnamed = categories_module.name_aliases_by_name()[categories_module.UNNAMED_PRODUCT_NAME]
#     aliases = unnamed.aliases
#     keyboard = ReplyKeyboardMarkup(selective=True)
#     buttons = [KeyboardButton(text=alias) for alias in aliases]
#     keyboard.add(*buttons)
#     await message.answer(f"Какому алиасу вы хотите назначить имя?", reply_markup=keyboard)
#     await UserStates.WAITING_FOR_FIRST_RESPONSE.set()
#     #
    #
    # target_string = re.search(".+\s(to|->)\s.+\S+", message.text)
    # if not target_string:
    #     await message.answer("Wrong format. Use alias to category")
    #     return
    # alias = re.search("(?<=/ro\s)\S+.+(?=\s->)", message.text)
    # if not alias:
    #     alias = re.search("(?<=/ro\s)\S+.+(?=\sto)", message.text)
    # alias = alias.group()
    #
    # category = re.search("(?<=->\s).+\S+", message.text)
    # if not category:
    #     category = re.search("(?<=to\s).+\S+", message.text).group()
    # category = category.group()
    # categories_module.set_new_name_to_alias(alias, category)
    # await message.answer(f"Successfullty transfered alias {alias} to {category} category")


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


class SetPriceStates(StatesGroup):
    WAITING_PRODUCT_NAME = State()
    WAITING_PRODUCT_NAME_2 = State()
    WAITING_NEW_PRICE = State()


SET_PRICE_VARIABLES = ["SET_PRICE_PRODUCT"]


@dp.message_handler(IsAdmin(), lambda message: message.text == "set price", state=AdminStates.INITIAL_STATE)
async def set_price(message: types.Message, state: FSMContext):
    await SetPriceStates.WAITING_PRODUCT_NAME.set()
    keyboard = get_keyboard(["first"])
    await message.answer(f"Введите часть имени продукта", reply_markup=keyboard)


@dp.message_handler(IsAdmin(), state=SetPriceStates.WAITING_PRODUCT_NAME)
async def set_price_chose_product(message: types.Message, state: FSMContext):
    product_name = message.text
    products = product_storage.get_products()
    product_names = [p.name for p in products]
    similar_product_names = get_most_similar_strings(product_name, product_names)[:10]
    keyboard = get_keyboard(similar_product_names)
    await SetPriceStates.WAITING_PRODUCT_NAME_2.set()
    await message.answer(f"Выберите продукт", reply_markup=keyboard)


@dp.message_handler(IsAdmin(), state=SetPriceStates.WAITING_PRODUCT_NAME_2)
async def set_price_chose_product_final(message: types.Message, state: FSMContext):
    product_name = message.text
    product = product_storage.get_product_by_name(product_name)
    if not product:
        return await message.answer(f"Нет такого продукта")
    await state.update_data({SET_PRICE_VARIABLES[0]: product})
    await SetPriceStates.WAITING_NEW_PRICE.set()
    await message.answer(f"Цена {product.price}\nВведите новую цену")


@dp.message_handler(IsAdmin(), state=SetPriceStates.WAITING_NEW_PRICE)
async def set_price_waiting_value(message: types.Message, state: FSMContext):
    value = message.text
    quantity = re.match(r'^[+-]?\d+(\.\d+)?$', value)
    if not quantity:
        await message.answer("Введите число в формате 331.12 или 232")
        return

    data = await state.get_data()
    product = data.get(SET_PRICE_VARIABLES[0])
    if not product:
        return
    product_storage.set_price(product.name, float(quantity.group()))
    await message.answer(f"Установили цену {quantity.group()} на {product.name}")



# @dp.message_handler(IsAdmin(), commands=['gm__'])
# async def get_messages(message: types.Message):
#     await message.answer(messages.get_messages())
#


@dp.message_handler(IsAdmin(), state=None)
async def get_initial_message(message: types.Message):
    keyboard = get_initial_keyboard()
    await AdminStates.INITIAL_STATE.set()
    await message.answer("Выберите действие", reply_markup=keyboard)

