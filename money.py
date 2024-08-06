""" Работа с расходами — их добавление, удаление, статистики"""
import users
from db_modules.db import DataBase
from typing import List
from aiogram.dispatcher.filters.state import StatesGroup, State

from pkg import new_action_get_id, ActionType, get_now_date

db = DataBase()


def add_storage(user: str, initial_amount: float=0):
    db.insert("money", {"user_name": user, "amount": initial_amount})


def get_money_recepients() -> List[str]:
    cursor = db.cursor
    cursor.execute("select user_name from money")
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def get_balance(user: str) -> float:
    cursor = db.cursor
    cursor.execute("select amount from money where user_name = (?)",
                   (user,))
    result = cursor.fetchone()
    if not result:
        return float(0)
    return round(float(result[0]), 2)


def increment(user: str, increment_val: float):
    balance = get_balance(user) + increment_val
    db.delete("money", {"user_name": user})
    add_storage(user, balance)


def transfer(amount: float, from_name: str, to_name: str, user_id: int=None):
    increment(from_name, -amount)
    increment(to_name, amount)
    if user_id:
        user = users.get_user_by_id(user_id)
        recieving_user = users.get_user_by_name(to_name)
        if from_name == "Касса":
            transfer_comment = f"{user.name} выдал {amount} лари для {to_name}"
            recieving_comment = f"{to_name} получил {amount} лари из Кассы от {user.name}"
            new_action_get_id(ActionType.MONEY_TRANSFER, user_id, get_now_date(), transfer_comment)
            if recieving_user:
                new_action_get_id(ActionType.MONEY_RECEIVING, recieving_user.user_id, get_now_date(), recieving_comment)
        else:
            transfer_comment = f"{user.name} переслал {amount} лари от {from_name} к {to_name}"
            recieving_comment = f"{to_name} получил {amount} лари от {user.name}"
            new_action_get_id(ActionType.MONEY_TRANSFER, user_id, get_now_date(), transfer_comment)
            if recieving_user:
                new_action_get_id(ActionType.MONEY_RECEIVING, recieving_user.user_id, get_now_date(), recieving_comment)



def balance_report() -> str:
    cursor = db.cursor
    cursor.execute("select user_name, amount from money")
    rows = cursor.fetchall()
    all_money = 0
    answers = []
    for row in rows:
        user, amount = row
        all_money += amount
        answers.append(f"{user}: {amount}")

    answers.append(f"Итого: {all_money}")
    return "\n".join(answers)
