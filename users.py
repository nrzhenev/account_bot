""" Работа с расходами — их добавление, удаление, статистики"""
from typing import List, NamedTuple, Optional

from db_modules.db import DataBase


db = DataBase()


class User(NamedTuple):
    user_id: int
    current_role_id: int
    name: str


def add_storage(user: str, initial_amount: float=0):
    db.insert("money", {"user_name": user, "amount": initial_amount})


def get_user_by_id(user_id: int) -> Optional[User]:
    cursor = db.cursor
    cursor.execute("select name, user_id, current_role_id from users where user_id = (?)",
                   (user_id,))
    result = cursor.fetchone()
    if not result:
        return
    name, user_id, current_role_id = result
    return User(user_id=user_id, current_role_id=current_role_id, name=name)


def get_user_by_name(name: str) -> Optional[User]:
    cursor = db.cursor
    cursor.execute("select name, user_id, current_role_id from users where name = (?)",
                   (name,))
    result = cursor.fetchone()
    if not result:
        return
    name, user_id, current_role_id = result
    return User(user_id=user_id, current_role_id=current_role_id, name=name)
