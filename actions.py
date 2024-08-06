""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, NamedTuple, Optional

import expenses as expenses_module
import users
from db_modules.db import DataBase
from pkg import ActionType

db = DataBase()


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str


class ActionInterface(ABC):
    @abstractmethod
    def action_info(self, *args) -> str:
        pass


class Action(ActionInterface):
    """Структура добавленного в БД нового расхода"""
    def __init__(self,
                 action_id: int,
                 user_id: int,
                 action_type: ActionType,
                 comment: str,
                 created: datetime.date):
        self.action_id = action_id
        self.user_id = user_id
        self.comment = comment
        self.created = created
        self.action_type = action_type


class MoneyAction(ActionInterface):
    """Структура добавленного в БД нового расхода"""

    def __init__(self,
                 action_id: int,
                 user_id: int,
                 action_type: ActionType,
                 comment: str,
                 created: datetime.date):
        self.action_id = action_id
        self.user_id = user_id
        self.comment = comment
        self.created = created
        self.action_type = action_type

    def action_info(self, user_info: bool, date_info: bool) -> str:
        raise NotImplementedError


    # def _get_additional_info_by_type(self) -> str:
    #     if self.action_type == ActionType.EXPENSE.name:
    #         exps = expenses.get_expenses_by_action_id(self.action_id)
    #         return expenses.expenses_string(exps)
    #     elif self.action_type == ActionType.RECEIVING.name:
    #         product_changes = product_storage.get_product_changes_by_action_id(self.action_id)
    #         return product_storage.volumes_string(product_changes)
    #     elif self.action_type == ActionType.WRITE_OFF.name:
    #         return ""
    #     elif self.action_type == ActionType.STAFF_WRITE_OFF.name:
    #         return ""

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.action_info()


class ExpenseAction(Action):
    def action_info(self, user_info: bool=True, date_info: bool=True) -> str:
        exps = expenses_module.get_expenses_by_action_id(self.action_id)
        expenses_by_user = defaultdict(list)
        for exp in exps:
            expenses_by_user[exp.user_id].append(exp)
        result = ""
        for user_id in expenses_by_user:
            user = users.get_user_by_id(user_id)
            expenses = expenses_by_user[user_id]
            user_string = ""
            date_string = ""
            if user_info:
                user_string = user.name + " "
            if date_info:
                date_string = f" {str(self.created)} числа"

            result += f"{user_string}потратил {expenses_module.expenses_sum(expenses)} лари{date_string}\n"
        return result


class WriteOffAction(Action):
    def action_info(self, user_info: bool, date_info: bool) -> str:
        return " "


class StaffWriteOffAction(Action):
    def action_info(self, user_info: bool, date_info: bool) -> str:
        return " "


class ReceivingAction(Action):
    def action_info(self, user_info: bool, date_info: bool) -> str:
        return self.comment


class MoneyTransferAction(Action):
    def action_info(self, user_info: bool, date_info: bool) -> str:
        return self.comment


class MoneyReceivingAction(Action):
    def action_info(self, user_info: bool, date_info: bool) -> str:
        return self.comment


def init_action(action_id: int, user_id: int, action_type: ActionType, comment: str, created: datetime.date):
    actions = {ActionType.EXPENSE: ExpenseAction,
               ActionType.RECEIVING: ReceivingAction,
               ActionType.WRITE_OFF: WriteOffAction,
               ActionType.STAFF_WRITE_OFF: StaffWriteOffAction,
               ActionType.MONEY_TRANSFER: MoneyTransferAction,
               ActionType.MONEY_RECEIVING: MoneyReceivingAction
               }
    action = actions[action_type](action_id, user_id, action_type, comment, created)
    return action


def get_actions_between_dates(date_from: Optional[datetime.date]=None,
                              date_to: Optional[datetime.date]=None,
                              action_type: Optional[ActionType]=None) -> List[Action]:
    cursor = db.cursor
    if not action_type:
        if date_from and date_to:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE date(?) <= date(created) AND date(created) <= date(?)",
                (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d')))
        elif date_from:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE date(?) <= date(created)",
                (date_from.strftime('%Y-%m-%d')))
        elif date_to:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE date(created) <= date(?)",
                (date_to.strftime('%Y-%m-%d')))
        else:
            cursor.execute("Select action_id, user_id, action_type, comment, created From actions")
    else:
        if date_from and date_to:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE date(?) <= date(created) AND date(created) <= date(?) AND action_type = ?",
                (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'), ActionType.EXPENSE.name))
        elif date_from:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE date(?) <= date(created) AND action_type = ?",
                (date_from.strftime('%Y-%m-%d'), ActionType.EXPENSE.name))
        elif date_to:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE date(created) <= date(?) AND action_type = ?",
                (date_to.strftime('%Y-%m-%d'), ActionType.EXPENSE.name))
        else:
            cursor.execute(
                "Select action_id, user_id, action_type, comment, created From actions WHERE action_type = ?",
                (ActionType.EXPENSE.name))
    all = cursor.fetchall()
    actions = []
    for action_row in all:
        actions.append(init_action(action_row[0], action_row[1], ActionType[action_row[2]], action_row[3], action_row[4]))
    return actions


# def get_today_actions(date: Optional[datetime.date]=None) -> List[Action]:
#     if not date:
#         now = get_now_date()
#     else:
#         now = date
#     beginning_of_day = datetime.datetime(now.year, now.month, now.day, 0)
#     actions = get_actions_between_dates(beginning_of_day, now)
#     return actions


def actions_string(actions: List[Action]) -> str:
    # actions_by_id = defaultdict(list)
    # for action in actions:
    #     actions_by_id[action.action_id].append(action)
    result_dict = defaultdict(lambda: defaultdict(list))
    for action in actions:
        #result_dict[action.user_id].append(action_id)
        result_dict[action.user_id][action.created].append(action)
    result = ""
    for user_id in result_dict:
        user = users.get_user_by_id(user_id)
        result += f"{user.name}:\n"
        #for action_type in result_dict[user_id]:
        for creation_date in result_dict[user_id]:
            result += str(creation_date)+ ":\n"
            #for created in result_dict[user_id][creation_date]:
            for action in result_dict[user_id][creation_date]:
                result += f"{action.action_info(False, False)}\n"
    return result
