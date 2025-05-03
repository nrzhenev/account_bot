import sqlite3
import os
import pytest
from unittest.mock import patch, MagicMock

# Импортируем тестируемые классы
from db_modules.db import DataBase, ProductRepository, DebtsRepository, ProductChangesRepository
from domain.product import ProductWithPrice
from domain.money_actor import MoneyActor


@pytest.fixture
def product_repo(temporary_db):
    """Фикстура для создания репозитория продуктов"""
    return ProductRepository(temporary_db)


@pytest.fixture
def debts_repo(temporary_db):
    """Фикстура для создания репозитория долгов"""
    return DebtsRepository(temporary_db)


@pytest.fixture
def product_changes_repo(temporary_db):
    """Фикстура для создания репозитория изменений продуктов"""
    return ProductChangesRepository(temporary_db)


@pytest.mark.db
class TestProductRepository:
    def test_get_by_id_not_found(self, product_repo):
        """Тест проверяет метод get_by_id, когда продукт не найден"""
        product = product_repo.get_by_id(999)
        assert product is None, "Продукт с несуществующим ID должен возвращать None"
    
    def test_get_by_id(self, temporary_db, product_repo):
        """Тест проверяет метод get_by_id, когда продукт найден"""
        # Вставим продукт
        temporary_db.insert("products", {"id": 1, "name": "тест", "measurement_unit": "кг"})
        
        product = product_repo.get_by_id(1)
        assert product is not None, "Продукт должен быть найден по ID"
        assert product.id == 1, f"ID продукта должен быть 1, получено: {product.id}"
        assert product.name == "тест", f"Имя продукта должно быть 'тест', получено: {product.name}"
        assert product.measurement_unit == "кг", f"Единица измерения должна быть 'кг', получено: {product.measurement_unit}"
    
    def test_get_by_name_not_found(self, product_repo):
        """Тест проверяет метод get_by_name, когда продукт не найден"""
        product = product_repo.get_by_name("несуществующий")
        assert product is None, "Продукт с несуществующим именем должен возвращать None"
    
    def test_get_by_name(self, temporary_db, product_repo):
        """Тест проверяет метод get_by_name, когда продукт найден"""
        # Вставим продукт
        temporary_db.insert("products", {"id": 1, "name": "тест", "measurement_unit": "кг"})
        
        product = product_repo.get_by_name("тест")
        assert product is not None, "Продукт должен быть найден по имени"
        assert product.id == 1, f"ID продукта должен быть 1, получено: {product.id}"
        assert product.name == "тест", f"Имя продукта должно быть 'тест', получено: {product.name}"
        assert product.measurement_unit == "кг", f"Единица измерения должна быть 'кг', получено: {product.measurement_unit}"
        assert isinstance(product.prices, list), f"Цены продукта должны быть списком, получено: {type(product.prices)}, {product.prices}"
    
    def test_get_all_empty(self, product_repo):
        """Тест проверяет метод get_all, когда нет продуктов"""
        products = product_repo.get_all()
        assert len(products) == 0, "Список продуктов должен быть пустым"
    
    def test_get_all(self, product_repo):
        """Тест проверяет метод get_all, когда есть продукты"""
        # Мокаем результат запроса
        product_repo.add_product("тест1", "кг")
        product_repo.add_product("тест2", "шт")

        products = product_repo.get_all()
        assert len(products) == 2, f"Должно быть 2 продукта, получено: {len(products)}"
        assert products[0].id == 1, f"ID первого продукта должен быть 1, получено: {products[0].id}"
        assert products[0].name == "тест1", f"Имя первого продукта должно быть 'тест1', получено: {products[0].name}"
        assert products[0].measurement_unit == "кг", f"Единица измерения первого продукта должна быть 'кг', получено: {products[0].measurement_unit}"
        assert products[1].id == 2, f"ID второго продукта должен быть 2, получено: {products[1].id}"
        assert products[1].name == "тест2", f"Имя второго продукта должно быть 'тест2', получено: {products[1].name}"
        assert products[1].measurement_unit == "шт", f"Единица измерения второго продукта должна быть 'шт', получено: {products[1].measurement_unit}"
    
    def test_add_product(self, temporary_db, product_repo):
        """Тест проверяет метод add_product"""
        product_repo.add_product("Новый продукт", "кг")
        
        # Проверяем, что продукт добавлен
        temporary_db.cursor.execute("SELECT name, measurement_unit FROM products WHERE name = 'новый продукт'")
        result = temporary_db.cursor.fetchone()
        assert result is not None, "Продукт должен быть добавлен в базу данных"
        assert result[0] == "новый продукт", f"Имя продукта должно быть 'новый продукт', получено: {result[0]}"
        assert result[1] == "кг", f"Единица измерения должна быть 'кг', получено: {result[1]}"


@pytest.mark.db
class TestDebtsRepository:
    def test_get_by_name_not_found(self, debts_repo):
        """Тест проверяет метод get_by_name, когда долг не найден"""
        debt = debts_repo.get_by_name("несуществующий")
        assert debt is None, "Долг с несуществующим именем должен возвращать None"
    
    def test_get_by_name(self, debts_repo):
        """Тест проверяет метод get_by_name, когда долг найден"""
        # Мокаем результат запроса
        debts_repo.set("Компания", 100.5)
        debt = debts_repo.get_by_name("Компания")
        assert debt is not None, "Долг должен быть найден по имени компании"
        assert debt.name == "Компания", f"Имя компании должно быть 'Компания', получено: {debt.name}"
        assert debt.amount == 100.5, f"Сумма долга должна быть 100.5, получено: {debt.amount}"
    
    def test_set(self, temporary_db, debts_repo):
        """Тест проверяет метод set"""
        debts_repo.set("Компания", 200.0)
        
        # Проверяем, что долг добавлен
        temporary_db.cursor.execute("SELECT company_name, amount FROM debts WHERE company_name = 'Компания'")
        result = temporary_db.cursor.fetchone()
        assert result is not None, "Долг должен быть добавлен в базу данных"
        assert result[0] == "Компания", f"Имя компании должно быть 'Компания', получено: {result[0]}"
        assert result[1] == 200.0, f"Сумма долга должна быть 200.0, получено: {result[1]}"


@pytest.mark.db
class TestProductChangesRepository:
    def test_initialization(self, product_changes_repo):
        """Проверяем корректную инициализацию репозитория"""
        assert product_changes_repo.db is not None, "БД в репозитории должна быть инициализирована"
        assert isinstance(product_changes_repo.pr, ProductRepository), f"pr должен быть экземпляром ProductRepository, получено: {type(product_changes_repo.pr)}"
    
    # Реализация метода increment_products в коде отсутствует,
    # поэтому мы не можем создать для него полноценный тест
    def test_increment_products_stub(self, product_changes_repo):
        """Заглушка для теста метода increment_products"""
        # Просто вызываем метод, чтобы удостовериться, что он существует
        result = product_changes_repo.increment_products()
        assert result is None, "Метод increment_products должен возвращать None"
