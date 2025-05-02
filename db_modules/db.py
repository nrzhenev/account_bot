import os

import sqlite3
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from db_modules.interface import ProductRepositoryInterface
from domain.product import ProductWithPrice


LOCAL_DB_NAME = "/home/nikita/git/account_bot/db/finance.db"


class DataBase:
    """Singleton"""
    _instances = {}

    def __new__(cls, path: str=LOCAL_DB_NAME):
        if not cls._instances.get(path):
            cls._instances[path] = super(DataBase, cls).__new__(cls)
        return cls._instances[path]

    def __init__(self, path: str=LOCAL_DB_NAME):
        self._existed = False
        if os.path.exists(path):
            self._existed = Tuple

        self.path = path
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self._init_db()

    def insert(self, table: str, column_values: Dict):
        columns = ', '.join( column_values.keys() )
        values = [tuple(column_values.values())]
        placeholders = ", ".join( "?" * len(column_values.keys()) )
        self.cursor.executemany(
            f"INSERT OR REPLACE INTO {table} "
            f"({columns}) "
            f"VALUES ({placeholders})",
            values)
        self.conn.commit()

    def update(self, table: str, new_dict: dict):
        keys = list(new_dict.keys())
        assert len(keys) == 2
        search_col, change_col = keys
        self.cursor.execute(
            f"UPDATE {table} "
            f"SET {change_col} = ? "
            f"WHERE {search_col} = ?",
            (new_dict[change_col], new_dict[search_col]))
        self.conn.commit()

    def fetchall(self, table: str, columns: List[str]) -> dict:
        columns_joined = ", ".join(columns)
        self.cursor.execute(f"SELECT {columns_joined} FROM {table}")
        rows = self.cursor.fetchall()
        result = defaultdict(list)
        for row in rows:
            for index, column in enumerate(columns):
                #dict_row[column] =
                result[column].append(row[index])
        return result

    def delete(self, table: str, value_by_column: dict) -> None:
        query = f"DELETE FROM {table} WHERE {' = ? AND '.join(list(value_by_column.keys()))} = ?"
        self.cursor.execute(query, tuple(value_by_column.values()))
        self.conn.commit()

    def _init_db(self):
        """Инициализирует БД"""
        if self._existed:
            return
        with open("createdb.sql", "r") as f:
            sql = f.read()
        self.cursor.executescript(sql)
        self.conn.commit()

    def check_db_exists(self):
        """Проверяет, инициализирована ли БД, если нет — инициализирует"""
        self.cursor.execute("SELECT name FROM sqlite_master "
                       "WHERE type='table' AND name='expense'")
        table_exists = self.cursor.fetchall()
        if table_exists:
            return
        self._init_db()


class ProductRepository(ProductRepositoryInterface):
    def __init__(self, data_base):
        self.db = data_base

    def get_by_id(self, id: int) -> Optional[ProductWithPrice]:
        cursor = self.db.cursor
        cursor.execute("select p.id, p.name, p.measurement_unit from products p where p.id = (?)",
                       (id,))
        result = cursor.fetchone()
        if not result:
            return
        prices_string = result[-1]
        return ProductWithPrice(*result, prices_string)

    def get_by_name(self, name: str) -> Optional[ProductWithPrice]:
        cursor = self.db.cursor
        cursor.execute(
            "select p.id, p.name, p.measurement_unit, IFNULL(GROUP_CONCAT(pp.price), '0') as prices from products p LEFT JOIN product_price pp on p.id = pp.product_id where p.name = (?)",
            (name,))
        result = cursor.fetchone()
        id, name, measurement_unit, prices = result
        if not (id and name):
            return
        return ProductWithPrice(*result[:-1], prices)

    def get_all(self) -> List[ProductWithPrice]:
        cursor = self.db.cursor
        cursor.execute(
            "select p.id, p.name, p.measurement_unit, IFNULL(GROUP_CONCAT(pp.price), '0') from products p LEFT JOIN product_price pp ON p.id = pp.product_id GROUP BY p.id")
        rows = cursor.fetchall()
        if not rows:
            return []

        return [ProductWithPrice(*row[:3], [float(price) for price in row[3].split(",")]) for row in rows]

    def add_product(self, name: str, measurement_unit: str):
        product_name = name.lower()
        self.db.insert("products",
                         {"name": product_name, "measurement_unit": measurement_unit})

#check_db_exists()
