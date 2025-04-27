import pytest
import sqlite3
from unittest.mock import patch

# Импортируем тестируемую функцию
from product_storage import add_product, get_product_by_name


class TestAddProduct:
    """Тесты для функции add_product"""
    
    def test_add_product(self, test_db):
        """Тест добавления нового продукта в базу данных"""
        product_name = "тестовый продукт"
        measurement_unit = "шт"
        
        add_product(product_name, measurement_unit, test_db)
        
        conn = sqlite3.connect(test_db.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, measurement_unit FROM products WHERE name = ?", (product_name,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None, "Продукт не был добавлен в базу данных"
        assert result[0] == product_name, f"Имя продукта '{result[0]}' не соответствует ожидаемому '{product_name}'"
        assert result[1] == measurement_unit, f"Единица измерения '{result[1]}' не соответствует ожидаемой '{measurement_unit}'"
    
    def test_add_product_lowercase(self, test_db):
        """Тест, что имя продукта преобразуется в нижний регистр при добавлении"""
        product_name = "ТЕСТОВЫЙ ПРОДУКТ"
        measurement_unit = "кг"
        
        add_product(product_name, measurement_unit, test_db)
        
        conn = sqlite3.connect(test_db.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE name = ?", (product_name.lower(),))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None, "Продукт не был добавлен в базу данных"
        assert result[0] == product_name.lower(), f"Имя продукта '{result[0]}' не в нижнем регистре"
