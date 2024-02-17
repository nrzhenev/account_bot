""" Работа с расходами — их добавление, удаление, статистики"""
from db_modules.db import DataBase

db = DataBase()


def add_storage(user: str, initial_amount: float=0):
    db.insert("money", {"user_name": user, "amount": initial_amount})


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


def transfer(amount: float, from_name: str, to_name: str):
    increment(from_name, -amount)
    increment(to_name, amount)


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
