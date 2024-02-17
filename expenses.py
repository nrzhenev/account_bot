""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from typing import List, NamedTuple, Optional
from collections import defaultdict

import regex as re
from aiogram import types

import money
import categories
import users
from db_modules.db import DataBase
from pkg import get_now_datetime, get_dates_from_string, get_now_formatted


db = DataBase()


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str


class Expense:
    """Структура добавленного в БД нового расхода"""
    def __init__(self,
                 amount: float,
                 category: str,
                 user_id: int,
                 created: datetime.date):
        self.amount = amount
        self.category = category
        self.user_id = user_id
        self.created = created

    def __repr__(self):
        return str(self)

    def __str__(self):
        user = users.get_user_by_id(self.user_id)
        return f"{self.amount}: {self.category}. ({self.created} - {user.name})"


#
# class ExpenseTable:
#     def __init__(self, db: db.DataBase, categories_table: Categories, money_table: money.MoneyTable):
#         self.db = db
#         self.money = money_table
#         self.categories_table = categories_table
#         self.last_id = 0
#         self.update()

# def _get_last_id():
#     cursor = db.cursor
#     cursor.execute("Select * From expense ORDER BY id desc limit 1")
#     result = cursor.fetchone()
#     if not result:
#         return 0
#     else:
#         id_, amount, product_alias, user_id, created = result
#         return id_

# def add_expense(amount: float, product_alias: str, user_id: int, date: datetime=get_now_formatted()):
#     new_id = _get_last_id() + 1
#     user = users.get_user_by_id(user_id)
#     money.increment(user.name, -abs(amount))
#     categories.add_alias(product_alias)
#     db.insert("expense", {"id": new_id,
#                                             "amount": amount,
#                                             "product_alias": product_alias,
#                                             "user_id": user_id,
#                                             "created": date})
def add_expense(expense: Expense):
    db.insert("expense", {"amount": expense.amount,
                                            "category": expense.category,
                                            "user_id": expense.user_id,
                                            "created": expense.created})
    user = users.get_user_by_id(expense.user_id)
    money.increment(user.name, -1*expense.amount)


def expenses_sum(expenses: List[Expense]) -> float:
    return sum([exp.amount for exp in expenses])


# def delete_expense(expense: Expense) -> None:
#     """Удаляет сообщение по его идентификатору"""
#     db.delete("expense", {"id": expense.id})


def get_expenses_between_dates(date_from: str, date_to) -> List[Expense]:
    date_from = get_dates_from_string(date_from)[0]
    date_to = get_dates_from_string(date_to)[0]
    cursor = db.cursor
    cursor.execute(
        "Select amount, category, user_id, created From expense WHERE date(?) <= date(created) AND date(created) <= date(?)",
        (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d')))
    all = cursor.fetchall()
    expenses = []
    for one in all:
        expenses.append(Expense(*one))
    return expenses


def last() -> List[Expense]:
    """Возвращает последние несколько расходов"""
    cursor = db.cursor
    cursor.execute(
        "select e.amount, c.category "
        "from expense e left join product_aliases c "
        "on c.alias=e.product_alias "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], product_alias=row[2], user_id=None, created=None) for row in
                     rows]
    return last_expenses


def get_expenses_by_date(date: str) -> List[Expense]:
    date = get_dates_from_string(date)[0]
    cursor = db.cursor
    cursor.execute("Select amount, category, user_id, created From expense WHERE date(created) = date(?)",
                   (date.strftime('%Y-%m-%d'),))
    all = cursor.fetchall()
    expenses = []
    for one in all:
        expenses.append(Expense(*one))
    return expenses


# def get_expenses_by_product_name(name: str) -> List[Expense]:
#     cursor = db.cursor
#     cursor.execute("Select e.id, e.amount, e.product_alias, e.user_id, e.created from expense e "
#                    "INNER JOIN product_aliases pa "
#                    "ON e.product_alias = pa.alias "
#                    "WHERE pa.name = ?", (name,))
#     all = cursor.fetchall()
#     result = []
#     for row in all:
#         result.append(Expense(*row))
#     return result


def expenses_by_user(expenses: List[Expense], user_id: int) -> List[Expense]:
    return [exp for exp in expenses if exp.user_id == user_id]
#
#

#
# def expenses_by_categories(expenses: List[Expense]) -> dict:
#     cursor = db.cursor
#     # cursor.execute("Select ca.category, SUM(e.amount) as total "
#     #                "From expense e "
#     #                "JOIN product_aliases ca ON "
#     #                "e.product_alias = ca.alias "
#     #                "GROUP BY ca.category;")
#     cursor.execute("Select name, alias from product_aliases")
#     res = cursor.fetchall()
#     name_by_alias = {}
#     for row in res:
#         name_by_alias[row[1]] = row[0]
#
#     result = defaultdict(list)
#     for expense in expenses:
#         result[name_by_alias[expense.product_alias]].append(expense)
#     return result

#
# def process_expenses_message(full_message: types.Message) -> List[Expense]:
#     """Добавляет новое сообщение.
#     Принимает на вход текст сообщения, пришедшего в бот."""
#     expenses_list = _expenses_from_message(full_message)
#     for expense in expenses_list:
#         add_expense(expense.amount, expense.product_alias, full_message.from_user.id)
#     return expenses_list


def get_today_expenses() -> List[Expense]:
    now = get_now_datetime()
    beginning_of_day = datetime.datetime(now.year, now.month, now.day, 0)
    expenses = get_expenses_between_dates(beginning_of_day.strftime("%d-%m-%Y"), now.strftime("%d-%m-%Y"))
    return expenses
#
#
def get_month_expenses() -> List[Expense]:
    now = get_now_datetime()
    first_day_of_month = get_dates_from_string(f'1-{now.month}-{now.year}')[0]
    first_day_string = first_day_of_month.strftime("%d-%m-%Y")
    now_string = now.strftime("%d-%m-%Y")
    expenses = get_expenses_between_dates(first_day_string, now_string)
    return expenses

# #
# def print_expenses(expenses: List[Expense], when_string:str="") -> str:
#     """Возвращает строкой статистику расходов за сегодня"""
#     exp_by_categories = expenses_by_categories(expenses)
#     sums_by_categories = {}
#     for item in exp_by_categories.items():
#         sums_by_categories[item[0]] = sum([float(expense.amount) for expense in item[1]])
#     result_string = ' лари\n'.join([f'{item[0]}: {item[1]}' for item in sums_by_categories.items()])
#     return (f"Расходы {when_string}:\n{result_string} лари")
# #
#
# def _parse_message(raw_message: str) -> List[Message]:
#     """Парсит текст пришедшего сообщения о новом расходе."""
#     regexp_result = re.findall(r"[\d]+ [^\d,.]+", raw_message)
#     result_messages = []
#
#     for result in regexp_result:
#         amount = re.search("\d+", result).group()
#         category_text = re.search("(?<=\d+\s).+", result).group()
#         amount = int(amount.strip(" ,."))
#         category_text = category_text.strip(" ,.")
#         result_messages.append(Message(amount=amount, category_text=category_text))
#     return result_messages

#
# def _expenses_from_message(message: types.Message) -> List[Expense]:
#     """Парсит текст пришедшего сообщения о новом расходе."""
#     regexp_result = re.findall(r"[\d]+ [^\d,.]+", message.text)
#     result_messages = []
#
#     for result in regexp_result:
#         amount = re.search("\d+", result).group()
#         category_text = re.search("(?<=\d+\s).+", result).group()
#         amount = int(amount.strip(" ,."))
#         category_text = category_text.strip(" ,.")
#         result_messages.append(Expense(amount=amount, product_alias=category_text, id=None, created=None, user_id=None))
#     return result_messages
#
#
# def _get_budget_limit() -> int:
#     """Возвращает дневной лимит трат для основных базовых трат"""
#     return 10000
