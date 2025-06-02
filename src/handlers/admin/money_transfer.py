import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import money
from src.handlers.admin import AdminStates, get_initial_keyboard
from pkg import dp, get_keyboard, verify_message_is_value, MONEY_VALUE_REGEX_STRING


class MoneyTransfer(StatesGroup):
    WAITING_SENDER_NAME = State()
    WAITING_RECEPIENT_NAME = State()
    WAITING_TRANSFER_QUANTITY = State()


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

    money.transfer(float(amount), sender, recepient, message.from_user.id)
    text = f"Перевел {recepient} {amount} лари от {sender}"
    await AdminStates.INITIAL_STATE.set()
    await message.answer(text, reply_markup=get_initial_keyboard())


@dp.message_handler(lambda message: message.text == "Перевести деньги", state=AdminStates.INITIAL_STATE)
async def transfer_money2(message: types.Message, state: FSMContext):
    senders = SENDERS
    keyboard = get_keyboard(senders)
    text = "Откуда перевести"
    await MoneyTransfer.WAITING_SENDER_NAME.set()
    await message.answer(text, reply_markup=keyboard)


SENDERS = ["Счет", "Никита"]
