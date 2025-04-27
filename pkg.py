import datetime
from typing import List, Optional
from enum import Enum, auto
import logging

import aiogram
import pytz
from Levenshtein import distance
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton
from dateparser.search import search_dates
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import re
from functools import wraps

from db_modules.db import DataBase
from credentials import TOKEN
from middlewares import AccessMiddleware

API_TOKEN = TOKEN

bot = Bot(token=API_TOKEN)
db = DataBase()
res = db.fetchall("users", ["user_id", "current_role_id", "name"])
ACCESS_IDS = {user_id: name for user_id, name in zip(res.get("user_id"), res.get("name"))}

dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(ACCESS_IDS))


def log_function_name(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling function: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


def message_handler(args):
    return dp.message_handler(*args)


MONEY_VALUE_REGEX_STRING = "\d+[,.]?\d*"


class ActionType(Enum):
    EXPENSE = "Траты"
    MONEY_TRANSFER = "Передача/Выдача денег"
    MONEY_RECEIVING = "Получение денег"
    STAFF_WRITE_OFF = "Списание стафф"
    WRITE_OFF = "Списание"
    RECEIVING = "Приемки"


def new_action_get_id(action_type: ActionType,
                      user_id: int,
                      date: Optional[datetime.date]=None,
                      comment: Optional[str]=None,
                      data_base=db) -> int:
    if not comment:
        comment = ""
    if not date:
        date = get_now_date()
    data_base.insert("actions", {"action_type": action_type.name, "user_id": user_id,
                          "created": date, "comment": comment})
    return max(data_base.fetchall("actions", ["action_id"])["action_id"])


async def verify_message_is_value(message) -> bool:
    if not re.match(MONEY_VALUE_REGEX_STRING, message.text):
        await message.answer("Сумма должна быть в формате 412.12 или 124,131 или 1241")
        return False
    return True


def get_now_date() -> datetime.date:
    tz = pytz.timezone("Asia/Tbilisi")
    now = datetime.datetime.now(tz)
    return now.date()


async def get_now_date_async(state) -> datetime.date:
    # Получение данных из контекста пользователя
    data = await state.get_data()
    date = data.get("date")
    if not date:
        return get_now_date()
    return date


def get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return get_now_date().strftime("%Y-%m-%d")


def save_message(data_base: DataBase, message: types.Message):
    user_id = message.from_user.id
    data_base.insert("messages",
              {
                  "user_id": user_id,
                  "created": get_now_formatted(),
                  "message": message.text
              })


def _get_dates_from_string(string: str, parsing_regime: str="DMY"):
    string = string.replace('.', ' ').strip()
    found_dates = search_dates(string, languages=['ru'], settings={'DATE_ORDER': parsing_regime,
                                                                   'TIMEZONE': 'UTC+4',
                                                                   'PREFER_DAY_OF_MONTH': 'first'})
    if found_dates:
        dates = [date[1] for date in found_dates]
        return dates
    return []


def get_dates_from_string(string: str, parsing_regime: str="DMY") -> List[datetime.datetime]:
    string = string.replace('.', ' ').strip()
    found_dates = search_dates(string, languages=['ru'], settings={'DATE_ORDER': parsing_regime,
                                                                   'TIMEZONE': 'UTC+4',
                                                                   'PREFER_DAY_OF_MONTH': 'first'})
    if found_dates:
        dates = [date[1] for date in found_dates]
        return dates
    return _get_dates_from_string(string, parsing_regime)


def _calc_dist_dictionary(short: str, long: str, dictionary=None, core_size=None) -> dict:
    if dictionary is None:
        dictionary = {}
    if core_size is None:
        core_size = len(long)
    if core_size < len(short):
        return dictionary
    short = short.lower()
    long = long.lower()
    for i in range(0, len(long) - core_size + 1):
        substring = long[i:i+core_size]
        dictionary[substring] = distance(short, substring)
    dictionary.update(_calc_dist_dictionary(short, long, dictionary, core_size - 1))
    return dictionary


def calc_dist(str1: str, str2: str):
    short, long = sorted([str1, str2], key=lambda string: len(string))
    distances_dictionary = _calc_dist_dictionary(short, long)
    string_length = len(short)
    length_difference_penalty = (len(long) - len(short))/len(long)
    if len(short) == 0:
        string_length = 0.1
    return (min(distances_dictionary.items(),
               key=lambda item: item[1]/string_length)[1] + length_difference_penalty)/string_length


def get_most_similar_strings(string: str, list_of_strings: List[str]):
    list_of_strings = sorted(list_of_strings, key=lambda string: len(string), reverse=True)
    return sorted(list_of_strings, key=lambda string2: calc_dist(string, string2))


def get_keyboard(texts: List[str], one_time: bool=False):
    keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=one_time)
    buttons = [KeyboardButton(text=text) for text in texts]
    keyboard.add(*buttons)
    return keyboard
