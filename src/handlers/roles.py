from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional


import expenses
import users
from db_modules.db import DataBase
from aiogram.types import Message
from aiogram.filters import Filter
import shipment
import categories


db = DataBase()


class Roles(Enum):
    EXPENSES = 1
    SHIPMENTS = 2
    COOK = 3
    ADMIN = 0


def role_by_id(role_id: int) -> Optional[Roles]:
    for role in Roles:
        if role.value == role_id:
            return role


def get_user_role(user_id: int) -> Roles:
    user = users.get_user_by_id(user_id)
    return role_by_id(user.current_role_id)


class RoleInterface(ABC):
    @abstractmethod
    def handle_message(self, message: Message):
        pass

    @abstractmethod
    def set_to_user(self, user_id: int):
        pass

    @property
    @abstractmethod
    def role_id(self) -> int:
        pass


def _get_current_role_id(db: DataBase, user_id: int) -> int:
    cursor = db.cursor
    cursor.execute("SELECT id, current_role "
                   f"FROM users "
                   f"where id={user_id}")
    result = cursor.fetchone()
    user_id, role = result
    return role


class Role(RoleInterface):
    def __init__(self, db: DataBase):
        self.db = db

    def handle_message(self, message: Message):
        raise NotImplementedError

    @property
    def role_id(self) -> int:
        raise NotImplementedError

    def set_to_user(self, user_id: int):
        cursor = self.db.cursor
        cursor.execute("update users "
                       f"set current_role = {self.role_id} "
                       f"where id={user_id}")
#
#
# class Shipments(Role):
#     def handle_message(self, message: Message):
#         expenses_list = expenses.add_expenses(message.text)
#         amount = sum([expense.amount for expense in expenses_list])
#         answer_message = (
#             f"Добавлены траты {amount} лари.\n\n"
#             f"{expenses.get_today_statistics()}")
#         return answer_message
#
#     @property
#     def role_id(self) -> int:
#         return 1


class Expenses(Role):
    def handle_message(self, message: Message):
        expenses_list = expenses.process_expenses_message(message)
        amount = sum([expense.amount for expense in expenses_list])
        exp_list = expenses.get_today_expenses()
        today_message = expenses.print_expenses(exp_list, "сегодня")
        answer_message = (
            f"Добавлены траты Всего {amount} лари.\n\n"
            f"{today_message}")
        return answer_message

    @property
    def role_id(self) -> int:
        return 2


class IsExpenses:
    def __init__(self, db: DataBase):
        self.db = db

    async def check(self, message: Message):
        user_id = message.from_user.id
        current_role = _get_current_role_id(self.db, user_id)
        if current_role == 2:
            return True
        return False


class IsAdmin:
    async def check(self, message: Message):
        user_id = message.from_user.id
        role = get_user_role(user_id)
        return role is Roles.ADMIN


class IsExpensesRole:
    async def check(self, message: Message):
        user_id = message.from_user.id
        role = get_user_role(user_id)
        return role is Roles.EXPENSES


class IsCookRole:
    async def check(self, message: Message):
        user_id = message.from_user.id
        role = get_user_role(user_id)
        return role is Roles.COOK


class IsShipmentsRole(Filter):
    async def __call__(self, message: Message):
        user_id = message.from_user.id
        role = get_user_role(user_id)
        return role is Roles.SHIPMENTS

#
# class Temp(Role):
#     def handle_message(self, message: Message):
#         expenses_list = expenses.add_expenses(message.text)
#         amount = sum([expense.amount for expense in expenses_list])
#         answer_message = (
#             f"Добавлены траты {amount} ари.\n\n"
#             f"{expenses.get_today_statistics()}")
#         return answer_message
#
#     @property
#     def role_id(self) -> int:
#         return 3