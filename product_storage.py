""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from typing import Optional, List

from db_modules.db import DataBase, ProductRepository, ProductChangesRepository, IngredientsRepository
from domain.product import ProductVolume, PosterIngredient
from pkg import ActionType

db = DataBase()


def add_product(product_name: str, measurement_unit: str, data_base=db):
    product_repository = ProductRepository(data_base)
    return product_repository.add_product(product_name, measurement_unit)


def get_product_in_storage_by_name(product_name: str, data_base=db) -> Optional[ProductVolume]:
    return get_product_by_name(product_name, data_base)


def get_product_by_name(product_name: str, data_base=db) -> Optional[PosterIngredient]:
    product_repository = ProductRepository(data_base)
    return product_repository.get_by_name(product_name)


def get_products(data_base=db) -> List[PosterIngredient]:
    product_repository = ProductRepository(data_base)
    return product_repository.get_all()


def get_product_by_id(product_id: int, data_base=db) -> Optional[PosterIngredient]:
    product_repository = ProductRepository(data_base)
    return product_repository.get_by_id(product_id)


def get_ingredient_by_id(ingredient_id: int, data_base=db):
    product_repository = IngredientsRepository(data_base)
    return product_repository.get_by_id(ingredient_id)


def increment_products(increments: List[ProductVolume],
                       user_id: int,
                       action_type: ActionType,
                       date: datetime.date,
                       comment: str=None,
                       data_base=db):
    pcr = ProductChangesRepository(data_base)
    pcr.increment_products(increments, user_id, action_type, date, comment)
