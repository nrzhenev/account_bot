"""Модуль для работы с таблицей категорий"""
import sqlite3
from typing import Dict, List, NamedTuple, Tuple
from dataclasses import dataclass

from db_modules.db import DataBase
from pkg import get_most_similar_strings

db = DataBase()


ALIASES_TABLE_NAME = "product_aliases"
UNNAMED_PRODUCT_NAME = "unnamed"


class NameAliases(NamedTuple):
    """Структура категории"""
    name: str
    aliases: Tuple[str]


def _del_alias(alias: str, product_name: str):
    db.delete(ALIASES_TABLE_NAME, {"name": product_name, "alias": alias})


def name_aliases_by_name() -> dict:
    cursor = db.cursor
    query = f"SELECT name, GROUP_CONCAT(alias) as list FROM {ALIASES_TABLE_NAME} GROUP BY name"
    cursor.execute(query)
    result = cursor.fetchall()
    name_aliases_by_name = {}
    for row in result:
        name, aliases = row
        aliases = aliases.split(",")
        aliases = list(filter(None, map(str.strip, aliases)))
        name_aliases_by_name[name] = NameAliases(name=name, aliases=tuple(aliases))
    return name_aliases_by_name


def add_alias(alias: str, product_name: str=UNNAMED_PRODUCT_NAME):
    try:
        db.insert(ALIASES_TABLE_NAME,
                  {"name": product_name, "alias": alias})
    except sqlite3.IntegrityError as e:
        return


def get_product_names(self) -> List[Dict]:
    """Возвращает справочник категорий."""
    return list(self.name_aliases_by_name.values())


def get_product_by_alias(alias: str) -> NameAliases:
    """Возвращает категорию по одному из её алиасов."""
    for product in name_aliases_by_name().values():
        if alias in product.aliases:
            return product
    db.insert(ALIASES_TABLE_NAME, {"name": UNNAMED_PRODUCT_NAME, "alias": alias})
    return name_aliases_by_name()[UNNAMED_PRODUCT_NAME]


def get_names_most_similar(name, length: int):
    names = list(name_aliases_by_name().keys())
    return get_most_similar_strings(name, names)[:length]


def _get_named_aliases():
    cursor = db.cursor
    query = f"SELECT alias FROM {ALIASES_TABLE_NAME} WHERE name != ?"
    cursor.execute(query, (UNNAMED_PRODUCT_NAME, ))
    result = cursor.fetchall()
    aliases = set()
    for row in result:
        aliases.add(row[0])
    return aliases


def get_aliases_most_similar(name, length: int):
    aliases = _get_named_aliases()
    return get_most_similar_strings(name, list(aliases))[:length]


def set_new_name_to_alias(alias: str, product_name: str, old_product_name: str= UNNAMED_PRODUCT_NAME):
    _del_alias(alias, old_product_name)
    add_alias(alias, product_name)
