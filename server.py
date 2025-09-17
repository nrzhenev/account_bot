"""Сервер Telegram бота, запускаемый непосредственно"""
import asyncio
import logging

import os
from dotenv import load_dotenv

from db_modules.db import DataBase
# from handlers.expenses import initial_handlers
# from handlers.priority_handlers import chr
# from handlers.admin.handlers import UserStates
from src.handlers.barmen.receiving_by_hand import barmen_router
from src.handlers.barmen.manage_products import barmen_router
from src.handlers.barmen.write_off_products import barmen_router
from src.handlers.expenses.initial_handlers import expenses_router
#from handlers.barmen.test import barmen_router
# import poster_storage
from pkg import dp, bot

#from handlers.cook.handlers import show_shipment


load_dotenv()
db = DataBase()
dp.include_router(barmen_router)
dp.include_router(expenses_router)


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
    cursor = db.cursor
    # cursor.execute("select id, name, measurement_unit, quantity from product_storage")
    cursor.execute("select target, category from category_links")


async def start_polling():
    await dp.start_polling(bot)

async def main():
    await start_polling()


if __name__ == '__main__':
    #ps = poster_storage.PosterStorage()
    #asyncio.run(ps.async_init())
    #pre_initialize()
    asyncio.run(main())
    os.remove(f"{os.getenv("ROOT_DIRECTORY")}/db/finance.db")
    print(1)