""" Работа с расходами — их добавление, удаление, статистики"""
from db_modules import db


def get_messages() -> str:
    cursor = db.get_cursor()
    cursor.execute("Select * from messages")
    result = cursor.fetchall()
    messages = []
    for row in result:
        messages.append(": ".join([str(i) for i in row]))
    return "\n\n".join(messages)