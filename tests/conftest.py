import pytest
import os
import sqlite3
from unittest.mock import MagicMock, patch

# Фикстура для создания тестовой базы данных
@pytest.fixture
def test_db():
    """Создает тестовую базу данных и возвращает соединение с ней"""
    # Создаем временную тестовую БД
    test_db_path = "tests/db/test_finance.db"
    
    # Убедимся, что директория существует
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
    
    # Удаляем существующую тестовую БД, если она есть
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Создаем соединение с новой БД
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Инициализируем БД из SQL-скрипта
    with open("createdb.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()
    
    # Патчим путь к базе данных для тестов
    with patch('db_modules.db.LOCAL_DB_NAME', test_db_path):
        yield test_db_path
    
    # Закрываем соединение после теста
    conn.close()
    
    # Опционально можно удалить тестовую БД после тестов
    # if os.path.exists(test_db_path):
    #     os.remove(test_db_path)

# Патчим модуль db, чтобы изолировать тесты от реальной базы данных
@pytest.fixture(autouse=True)
def mock_db():
    """Автоматически патчит базу данных во всех тестах"""
    with patch('db_modules.db.DataBase') as mock_db:
        mock_db_instance = MagicMock()
        mock_cursor = MagicMock()
        mock_db_instance.cursor = mock_cursor
        mock_db.return_value = mock_db_instance
        yield mock_db_instance

# Фикстура для создания экземпляра ProductWithPrice
@pytest.fixture
def product_with_price():
    """Возвращает тестовый экземпляр ProductWithPrice"""
    from product_storage import ProductWithPrice
    return ProductWithPrice(1, "test_product", "kg", [10.0, 20.0, 30.0])

# Фикстура для создания экземпляра Product
@pytest.fixture
def product():
    """Возвращает тестовый экземпляр Product"""
    from product_storage import Product
    return Product(1, "test_product", "kg")

# Фикстура для создания тестового дерева категорий
@pytest.fixture
def category_tree():
    """Возвращает тестовое дерево категорий"""
    from product_storage import CategoriesTree, Node
    
    # Создаем дерево без обращения к бд
    tree = CategoriesTree.__new__(CategoriesTree)
    tree.nodes = {}
    tree.nodes_without_parent = {}
    tree.root = Node("root")
    
    # Добавляем структуру дерева для тестирования
    parent1 = Node("parent1")
    parent2 = Node("parent2")
    child1 = Node("child1")
    child2 = Node("child2")
    
    tree.root.add_child(parent1)
    tree.root.add_child(parent2)
    parent1.add_child(child1)
    parent2.add_child(child2)
    
    tree.nodes = {
        "child1": child1,
        "child2": child2,
    }
    
    tree.nodes_without_parent = {
        "parent1": parent1,
        "parent2": parent2,
    }
    
    return tree 