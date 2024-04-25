"""Сервер Telegram бота, запускаемый непосредственно"""
import asyncio
import logging
import time

from aiogram import executor

#import poster_storage
from pkg import dp
from product_storage import CategoriesTree
from db_modules.db import DataBase
from handlers.priority_handlers import chr
from handlers.admin.handlers import UserStates
from handlers.expenses.handlers import save_message
from handlers.barmen.handlers import get_keyboard
from handlers.cook.handlers import show_shipment


db = DataBase()


expenses_ = '⚙️ Вносить траты'
shipments_ = '🚚 Вносить поставки'
other = '❓ Вопросы'


logging.basicConfig(level=logging.INFO)


# @dp.message_handler(lambda message: message.text.startswith('/del'))
# async def del_expense(message: types.Message):
#     """Удаляет одну запись о расходе по её идентификатору"""
#     row_id = int(message.text[4:])
#     expenses.delete_expense(row_id)
#     answer_message = "Удалил"
#     await message.answer(answer_message)


# @dp.message_handler(commands=['categories'])
# async def categories_list(message: types.Message):
#     """Отправляет список категорий расходов"""
#     categories = categories_module.get_all_categories()
#     answer_message = "Категории трат:\n\n* " +\
#             ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in categories]))
#     await message.answer(answer_message)


# @dp.message_handler(IsAdmin(), commands=['due__'])
# async def delete_user_expenses(message: types.Message):
#     e = expenses.get_month_expenses()
#     e = expenses.expenses_by_user(e, message.from_user.id)
#     expenses.delete_expenses(e)


#
# @dp.message_handler(commands=['expenses'])
# async def list_expenses(message: types.Message):
#     """Отправляет последние несколько записей о расходах"""
#     ebc = expenses.expenses_by_categories()
#     if not ebc:
#         await message.answer("Расходы ещё не заведены")
#         return
#
#     last_expenses_rows = [
#         f"{i[0]}: {i[1]} лари\n"
#         for i in ebc.items()]
#     answer_message = "Все траты:\n\n* " + "\n\n* "\
#             .join(last_expenses_rows)
#     await message.answer(answer_message)


# @dp.message_handler(commands=['expenses'])
# async def list_expenses(message: types.Message):
#     """Отправляет последние несколько записей о расходах"""
#     et = expenses.ExpenseTable()
#     et.update()
#     last_expenses = expenses.last()
#     if not last_expenses:
#         await message.answer("Расходы ещё не заведены")
#         return
#
#     last_expenses_rows = [
#         f"{expense.amount} руб. на {expense.product_alias} — нажми "
#         f"/del{expense.id} для удаления"
#         for expense in last_expenses]
#     answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* "\
#             .join(last_expenses_rows)
#     await message.answer(answer_message)


def pre_initialize():
    tree = CategoriesTree()
    cursor = db.cursor
    # cursor.execute("select id, name, measurement_unit, quantity from product_storage")
    cursor.execute(
        "select target, category from category_links")
    rows = cursor.fetchall()
    tree.build_tree(rows)


def start_polling():
    try:
        executor.start_polling(dp, skip_updates=True)
    except:
        logging.warning("Trying to reconnect")
        time.sleep(5)
        start_polling()


import os


if __name__ == '__main__':
    #ps = poster_storage.PosterStorage()
    #asyncio.run(ps.async_init())
    #pre_initialize()
    start_polling()
    #os.remove("/home/rzhenev/personal/account_bot/db/finance.db")
    print(1)