import datetime
from typing import List

import pytz
from Levenshtein import distance
from aiogram import Bot, Dispatcher, types
from dateparser.search import search_dates
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db_modules.db import DataBase
from credentials import TOKEN
from middlewares import AccessMiddleware

IDS = {358058423: "Никита", 1268471021: "Мириан", 5852542325: "Коля", 368555562: "Юля", 651083072: "Миша", 5389969711: "Илья"}
API_TOKEN = TOKEN
ACCESS_IDS = IDS

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(ACCESS_IDS))


def get_now_datetime() -> datetime.date:
    """Возвращает сегодняшний datetime с учётом времненной зоны Мск."""
    tz = pytz.timezone("Asia/Tbilisi")
    now = datetime.datetime.now(tz)
    return now.date()


def get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return get_now_datetime().strftime("%Y-%m-%d")


def save_message(db: DataBase, message: types.Message):
    user_id = message.from_user.id
    db.insert("messages",
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


data_base = DataBase()


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
