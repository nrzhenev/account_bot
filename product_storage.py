""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from collections import defaultdict
from typing import Optional, List

import regex as re

from db_modules.db import DataBase, ProductRepository
from domain.product import Product, ProductWithPrice, ProductVolume, ProductVolumeWithPrice
from pkg import new_action_get_id, ActionType, db

db = DataBase()


def add_product(product_name: str, measurement_unit: str, data_base=db):
    product_name = product_name.lower()
    data_base.insert("products",
              {"name": product_name, "measurement_unit": measurement_unit})


def get_product_in_storage_by_name(product_name: str, data_base=db) -> Optional[ProductVolume]:
    return get_product_by_name(product_name, data_base)


def get_product_by_name(product_name: str, data_base=db) -> Optional[ProductWithPrice]:
    product_repository = ProductRepository(data_base)
    return product_repository.get_by_name(product_name)


def get_products(data_base=db) -> List[ProductWithPrice]:
    product_repository = ProductRepository(data_base)
    return product_repository.get_all()


def get_product_by_id(product_id: int, data_base=db) -> Optional[ProductWithPrice]:
    product_repository = ProductRepository(data_base)
    return product_repository.get_by_id(product_id)


def increment(product_name: str, increment: float, action_id: int, data_base=db):
    product = get_product_in_storage_by_name(product_name, data_base)
    if not product:
        return

    #quantity = product.quantity + increment
    db.insert("product_changes", {"product_id": product.product_id, "quantity": increment, "action_id": action_id})
    #db.delete("product_storage", {"name": product.name})
    #add_product(product.name, product.measurement_unit, quantity)


def get_product_changes_by_action_id(action_id: int, data_base=db) -> List[ProductVolumeWithPrice]:
    cursor = data_base.cursor
    cursor.execute(
        "select p.id, p.name, p.measurement_unit, p.price, SUM(pc.quantity) from products p join product_changes pc on p.id = pc.product_id where pc.action_id = (?) group by p.id",
        (action_id,))
    res = cursor.fetchall()
    result = []
    for row in res:
        pid, pname, measurement_unit, price, quantity = row
        result.append(ProductVolumeWithPrice(ProductWithPrice(pid, pname, measurement_unit, prices), quantity))
    return result


def increment_products(increments: List[ProductVolume],
                       user_id: int,
                       action_type: ActionType,
                       date: datetime.date,
                       comment: str=None,
                       data_base=db):
    if not comment:
        comment = ""
    action_id = new_action_get_id(action_type, user_id, date=date, comment=comment)
    for inc in increments:
        product = get_product_by_id(inc.product_id, data_base)
        increment(product.name, inc.quantity, action_id)


def set_price(product_name: str, new_price: float, data_base=db):
    product = get_product_by_name(product_name, data_base)
    data_base.insert("product_price", {"product_id": product.id, "price": new_price})
