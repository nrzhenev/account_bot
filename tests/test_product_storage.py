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
        
        add_product(product_name, measurement_unit)
        
        conn = sqlite3.connect(test_db)
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
        
        add_product(product_name, measurement_unit)
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE name = ?", (product_name.lower(),))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None, "Продукт не был добавлен в базу данных"
        assert result[0] == product_name.lower(), f"Имя продукта '{result[0]}' не в нижнем регистре"
    
    def test_add_product_with_get_product(self, test_db):
        """Тест, что добавленный продукт можно получить через функцию get_product_by_name"""
        product_name = "тестовый продукт для get"
        measurement_unit = "л"
        
        add_product(product_name, measurement_unit)
        
        product = get_product_by_name(product_name)
        
        assert product is not None, "Продукт не был найден функцией get_product_by_name"
        assert product.name == product_name, f"Имя продукта '{product.name}' не соответствует ожидаемому '{product_name}'"
        assert product.measurement_unit == measurement_unit, f"Единица измерения '{product.measurement_unit}' не соответствует ожидаемой '{measurement_unit}'" 