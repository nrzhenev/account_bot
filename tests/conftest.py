import pytest
import os
import sqlite3
from unittest.mock import MagicMock, patch

from db_modules.db import DataBase


# Фикстура для создания тестовой базы данных
@pytest.fixture
def temporary_db():
    """Создает тестовую базу данных и возвращает соединение с ней"""
    db_dir = "/home/nikita/git/account_bot/tests/db"
    test_db_path = f"{db_dir}/test_finance.db"

    # Убедимся, что директория существует
    os.makedirs(os.path.dirname(db_dir), exist_ok=True)

    os.chmod(db_dir, 0o777)

    # Удаляем существующую тестовую БД, если она есть
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    yield DataBase(test_db_path)
    
    # Опционально можно удалить тестовую БД после тестов
    # if os.path.exists(test_db_path):
    #     os.remove(test_db_path)

# # Патчим модуль db, чтобы изолировать тесты от реальной базы данных
# @pytest.fixture(autouse=True)
# def mock_db():
#     """Автоматически патчит базу данных во всех тестах"""
#     with patch('db_modules.db.DataBase') as mock_db:
#         mock_db_instance = MagicMock()
#         mock_cursor = MagicMock()
#         mock_db_instance.cursor = mock_cursor
#         mock_db.return_value = mock_db_instance
#         yield mock_db_instance

# Фикстура для создания экземпляра ProductWithPrice
@pytest.fixture
def product_with_price():
    """Возвращает тестовый экземпляр ProductWithPrice"""
    from domain.product import ProductWithPrice
    return ProductWithPrice(1, "test_product", "kg", [10.0, 20.0, 30.0])

# Фикстура для создания экземпляра Product
@pytest.fixture
def product():
    """Возвращает тестовый экземпляр Product"""
    from domain.product import Product
    return Product(1, "test_product", "kg")
