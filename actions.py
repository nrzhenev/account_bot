""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from collections import defaultdict
from typing import List, NamedTuple, Optional
from abc import ABC, abstractmethod

import money
import expenses
import product_storage
import users
from db_modules.db import DataBase
from pkg import get_now_date, get_dates_from_string, ActionType, new_action_get_id

db = DataBase()


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str


class Action:
    """Структура добавленного в БД нового расхода"""
    def __init__(self,
                 action_id: int,
                 user_id: int,
                 action_type: ActionType,
                 comment: str,
                 created: datetime.date):
        self.action_id = action_id
        self.user_id = user_id
        self.action_type = action_type
        self.comment = comment
        self.created = created

    def _get_additional_info_by_type(self) -> str:
        if self.action_type == ActionType.EXPENSE.name:
            exps = expenses.get_expenses_by_action_id(self.action_id)
            return expenses.expenses_string(exps)
        elif self.action_type == ActionType.RECEIVING.name:
            product_changes = product_storage.get_product_changes_by_action_id(self.action_id)
            return product_storage.volumes_string(product_changes)
        elif self.action_type == ActionType.WRITE_OFF.name:
            return ""
        elif self.action_type == ActionType.STAFF_WRITE_OFF.name:
            return ""

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self._get_additional_info_by_type()


class ActionFactory:
    def __init__(self,
                 action_id: int,
                 user_id: int,
                 action_type: ActionType,
                 comment: str,
                 created: datetime.date):
        pass


class Action(ABC):
    pass


def add_expense(expense: Action,
                date: datetime.date=get_now_date(),
                comment: Optional[str]=None):
    if not comment:
        comment = ""
    action_id = new_action_get_id(ActionType.EXPENSE, expense.user_id, date, comment)
    db.insert("expense", {"amount": expense.amount,
                                            "category": expense.category,
                                            "action_id": action_id})
    user = users.get_user_by_id(expense.user_id)
    money.increment(user.name, -1*expense.amount)


def expenses_sum(expenses: List[Action]) -> float:
    return sum([exp.amount for exp in expenses])


def get_actions_between_dates(date_from: datetime.date, date_to: datetime.date, action_type: Optional[ActionType]=None) -> List[Action]:
    cursor = db.cursor
    if not action_type:
        cursor.execute(
            "Select action_id, user_id, action_type, comment, created From actions WHERE date(?) <= date(created) AND date(created) <= date(?)",
            (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d')))
    else:
        cursor.execute(
            "Select action_id, user_id, action_type, comment, created From actions WHERE date(?) <= date(created) AND date(created) <= date(?) AND action_type = ?",
            (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'), ActionType.EXPENSE.name))
    all = cursor.fetchall()
    actions = []
    for one in all:
        actions.append(Action(one[0], one[1], ActionType[one[2]], one[3], one[4]))
    return actions


def sort_by_type(actions: List[Action]):
    result = defaultdict(list)
    for action in actions:
        result[action.action_type].append(action)
    return result


def last() -> List[Action]:
    """Возвращает последние несколько расходов"""
    cursor = db.cursor
    cursor.execute(
        "select e.amount, c.category "
        "from expense e left join product_aliases c "
        "on c.alias=e.product_alias "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [Action(id=row[0], amount=row[1], product_alias=row[2], user_id=None, created=None) for row in
                     rows]
    return last_expenses


def get_expenses_by_date(date: str) -> List[Action]:
    date = get_dates_from_string(date)[0]
    cursor = db.cursor
    cursor.execute("Select amount, category, user_id, created From expense WHERE date(created) = date(?)",
                   (date.strftime('%Y-%m-%d'),))
    all = cursor.fetchall()
    expenses = []
    for one in all:
        expenses.append(Action(*one))
    return expenses


def expenses_by_user(expenses: List[Action], user_id: int) -> List[Action]:
    return [exp for exp in expenses if exp.user_id == user_id]


def get_today_actions(date: Optional[datetime.date]=None) -> List[Action]:
    if not date:
        now = get_now_date()
    else:
        now = date
    beginning_of_day = datetime.datetime(now.year, now.month, now.day, 0)
    actions = get_actions_between_dates(beginning_of_day, now)
    return actions


def get_month_expenses(date: Optional[datetime.date] = None) -> List[Action]:
    if not date:
        now = get_now_date()
    else:
        now = date
    first_day_of_month = get_dates_from_string(f'1-{now.month}-{now.year}')[0]
    first_day = first_day_of_month
    expenses = get_actions_between_dates(first_day, now)
    return expenses


def actions_string(actions: List[Action]) -> str:
    result_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for action in actions:
        result_dict[action.user_id][action.action_type][action.created].append(action)
    result = ""
    for user_id in result_dict:
        result += f"{user_id}:\n"
        for action_type in result_dict[user_id]:
            result += action_type.value + ":\n"
            for created in result_dict[user_id][action_type]:
                result += created + f":{result_dict[user_id][action_type][created]}\n"
    return result
