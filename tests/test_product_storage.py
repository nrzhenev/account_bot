import sqlite3

import pytest

# Импортируем тестируемую функцию
from db_modules.db import ProductRepository


@pytest.mark.add_product
class TestAddProduct:
    """Тесты для функции add_product"""
    
    def test_add_product(self, test_db):
        """Тест добавления нового продукта в базу данных"""
        product_name = "test product"
        measurement_unit = "шт"

        pr = ProductRepository(test_db)
        pr.add_product(product_name, measurement_unit)
        
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
        product_name = "test product"
        measurement_unit = "кг"

        pr = ProductRepository(test_db)
        pr.add_product(product_name, measurement_unit)
        
        conn = sqlite3.connect(test_db.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE name = ?", (product_name.lower(),))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None, "Продукт не был добавлен в базу данных"
        assert result[0] == product_name.lower(), f"Имя продукта '{result[0]}' не в нижнем регистре"


@pytest.mark.get_product
class TestGetProduct:
    """Тесты для функций получения продукта из базы данных"""

    def test_get_product_by_name(self, test_db):
        """Тест получения продукта по имени"""
        # Добавляем тестовый продукт
        product_name = "test prodiuct"
        measurement_unit = "шт"
        test_db.insert("products", {"name": product_name, "measurement_unit": measurement_unit})

        # Получаем продукт
        pr = ProductRepository(test_db)
        product = pr.get_by_name(product_name)

        assert product is not None, "Продукт не найден"
        assert product.name == product_name, f"Имя продукта '{product.name}' не соответствует ожидаемому '{product_name}'"
        assert product.measurement_unit == measurement_unit, f"Единица измерения '{product.measurement_unit}' не соответствует ожидаемой '{measurement_unit}'"

    def test_get_product_by_name_not_found(self, test_db):
        """Тест случая, когда продукт не найден"""
        pr = ProductRepository(test_db)
        product = pr.get_by_name("несуществующий продукт")
        assert product is None, "Для несуществующего продукта должно возвращаться None"

    def test_get_product_by_id(self, test_db):
        """Тест получения продукта по ID"""
        # Добавляем тестовый продукт
        product_name = "test product"
        measurement_unit = "шт"
        test_db.insert("products", {"name": product_name, "measurement_unit": measurement_unit})

        # Получаем продукт
        pr = ProductRepository(test_db)
        product = pr.get_by_name(product_name)
        product_id = product.id
        product_by_id = pr.get_by_id(product_id)
        product = product_by_id

        assert product_by_id is not None, "Продукт не найден"
        assert product.id is not None, f"ID продукта '{product.id}' пустой'"
        assert product.name == product_name, f"Имя продукта '{product.name}' не соответствует ожидаемому '{product_name}'"
        assert product.measurement_unit == measurement_unit, f"Единица измерения '{product.measurement_unit}' не соответствует ожидаемой '{measurement_unit}'"

    def test_get_product_by_id_not_found(self, test_db):
        """Тест случая, когда продукт не найден по ID"""
        pr = ProductRepository(test_db)
        product = pr.get_by_id(999999)
        assert product is None, "Для несуществующего ID должно возвращаться None"

    def test_get_products(self, test_db):
        """Тест получения списка всех продуктов"""
        # Добавляем тестовые продукты
        pr = ProductRepository(test_db)

        products = [
            ("продукт 1", "шт"),
            ("продукт 2", "кг"),
            ("продукт 3", "л")
        ]
        for name, unit in products:
            test_db.insert("products", {"name": name, "measurement_unit": unit})

        # Получаем список продуктов
        result = pr.get_all()

        assert len(result) == len(products), "Количество полученных продуктов не соответствует ожидаемому"
        for product in result:
            assert any(p[0] == product.name and p[1] == product.measurement_unit for p in products), f"Продукт {product.name} не найден в тестовых данных"

    def test_get_products_empty(self, test_db):
        """Тест получения списка продуктов из пустой базы"""
        pr = ProductRepository(test_db)
        result = pr.get_all()
        assert len(result) == 0, "Для пустой базы должен возвращаться пустой список"
