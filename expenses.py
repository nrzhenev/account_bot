""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from collections import defaultdict
from typing import List, NamedTuple, Optional

import money
import users
from db_modules.db import DataBase
from pkg import get_now_date, get_dates_from_string, ActionType, new_action_get_id
from auxiliary.system_functions import TEXT_PARSERS

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


def add_expense(expense: Expense,
                date: datetime.date,
                comment: Optional[str]=None):
    if not comment:
        comment = ""
    action_id = new_action_get_id(ActionType.EXPENSE, expense.user_id, date, comment)
    db.insert("expense", {"amount": expense.amount,
                                            "category": expense.category,
                                            "action_id": action_id})
    user = users.get_user_by_id(expense.user_id)
    money.increment(user.name, -1*expense.amount)


def expenses_sum(expenses: List[Expense]) -> float:
    return sum([exp.amount for exp in expenses])


def get_expenses_between_dates(date_from: str, date_to) -> List[Expense]:
    date_from = get_dates_from_string(date_from)[0]
    date_to = get_dates_from_string(date_to)[0]
    cursor = db.cursor
    cursor.execute(
        "Select amount, category, user_id, created From expense e join actions a on e.action_id = a.action_id  WHERE date(?) <= date(created) AND date(created) <= date(?) AND a.action_type = ?",
        (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'), ActionType.EXPENSE.name))
    all = cursor.fetchall()
    expenses = []
    for one in all:
        expenses.append(Expense(*one))
    return expenses


def get_expenses_by_action_id(action_id: int):
    cursor = db.cursor
    cursor.execute(
        "Select amount, category, user_id,"
        " created From expense e join actions a on e.action_id = a.action_id  WHERE a.action_id = ?",
        (action_id,))
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


def expenses_by_user(expenses: List[Expense], user_id: int) -> List[Expense]:
    return [exp for exp in expenses if exp.user_id == user_id]


def get_today_expenses(date: Optional[datetime.date]=None) -> List[Expense]:
    if not date:
        now = get_now_date()
    else:
        now = date
    beginning_of_day = datetime.datetime(now.year, now.month, now.day, 0)
    expenses = get_expenses_between_dates(beginning_of_day.strftime("%d-%m-%Y"), now.strftime("%d-%m-%Y"))
    return expenses


def get_month_expenses(date: Optional[datetime.date] = None) -> List[Expense]:
    if not date:
        now = get_now_date()
    else:
        now = date
    first_day_of_month = get_dates_from_string(f'1-{now.month}-{now.year}')[0]
    first_day_string = first_day_of_month.strftime("%d-%m-%Y")
    now_string = now.strftime("%d-%m-%Y")
    expenses = get_expenses_between_dates(first_day_string, now_string)
    return expenses


def expenses_string(expenses: List[Expense], parsing_mode="HTML"):
    bold = TEXT_PARSERS[parsing_mode]["bold"]
    italic = TEXT_PARSERS[parsing_mode]["italic"]
    underlined = TEXT_PARSERS[parsing_mode]["underline"]
    result_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for expense in expenses:
        result_dict[expense.created][expense.user_id][expense.category] += expense.amount
    result = ""
    for created in sorted(result_dict):
        result += "\n\n" + bold(created) + ":\n"
        for user_id in result_dict[created]:
            user = users.get_user_by_id(user_id)
            result += f"{underlined(italic(user.name))}:\n"
            for category in result_dict[created][user_id]:
                result += category + f":{result_dict[created][user_id][category]}\n"
    return result


def filter_expenses(expenses: List[Expense], filter_function) -> List[Expense]:
    result = []
    for expense in expenses:
        if _ := filter_function(expense):
            result.append(_)
    return result
