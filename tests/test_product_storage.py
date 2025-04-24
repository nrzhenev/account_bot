import pytest
import datetime
from unittest.mock import MagicMock, patch
import numpy as np
from collections import defaultdict

from product_storage import (
    Node, CategoriesTree, Product, ProductWithPrice, ProductVolume, ProductVolume2, 
    ProductVolumeWithPrice, parse_add_product_message, add_product, get_products_in_storage,
    get_product_changes, get_products_by_category, get_product_in_storage_by_name,
    get_product_by_name, get_products, get_product_by_id, get_product_by_id_v0,
    increment, get_product_changes_by_action_id, increment_products, volumes_cost_sum,
    set_price, volumes_string, get_product_categories_v0, get_product_categories,
    get_product_categories_cook, get_product_categories_expenses
)

# Тесты для класса Node
class TestNode:
    def test_init(self):
        """Тест инициализации Node"""
        node = Node("test_key")
        assert node.key == "test_key"
        assert node.children == []
    
    def test_add_child(self):
        """Тест добавления дочернего узла"""
        parent = Node("parent")
        child = Node("child")
        parent.add_child(child)
        assert parent.children == [child]
    
    def test_repr(self):
        """Тест строкового представления узла"""
        node = Node("test_key")
        assert str(node) == "test_key"
    
    def test_print(self, capsys):
        """Тест метода печати узла"""
        root = Node("root")
        child = Node("child")
        root.add_child(child)
        
        root.print()
        captured = capsys.readouterr()
        assert "root" in captured.out
        assert " child" in captured.out

# Тесты для класса CategoriesTree
@pytest.fixture
def mock_db_cursor():
    """Фикстура для мока курсора базы данных"""
    with patch('product_storage.db.cursor') as mock_cursor:
        mock_cursor.fetchall.return_value = [("child1", "parent1"), ("child2", "parent1")]
        yield mock_cursor

class TestCategoriesTree:
    def test_init(self, mock_db_cursor):
        """Тест инициализации дерева категорий"""
        tree = CategoriesTree("test_category")
        assert tree.root.key == "root"
        assert isinstance(tree.nodes, dict)
        assert isinstance(tree.nodes_without_parent, dict)
        mock_db_cursor.execute.assert_called_once()
    
    def test_add_edge(self):
        """Тест добавления ребра в дереве"""
        tree = CategoriesTree.__new__(CategoriesTree)
        tree.nodes = {}
        tree.nodes_without_parent = {}
        tree.root = Node("root")
        
        tree.add_edge("parent", "child")
        
        assert "child" in tree.nodes
        assert "parent" in tree.nodes_without_parent
    
    def test_build_tree(self):
        """Тест построения дерева из рёбер"""
        tree = CategoriesTree.__new__(CategoriesTree)
        tree.nodes = {}
        tree.nodes_without_parent = {}
        tree.root = Node("root")
        
        edges = [("child1", "parent1"), ("child2", "parent1")]
        tree.build_tree(edges)
        
        assert "child1" in tree.nodes
        assert "child2" in tree.nodes
        assert "parent1" in tree.nodes_without_parent
    
    def test_print_tree(self, capsys):
        """Тест метода печати дерева категорий"""
        tree = CategoriesTree.__new__(CategoriesTree)
        tree.nodes = {}
        tree.nodes_without_parent = {}
        tree.root = Node("root")
        
        parent = Node("parent")
        child = Node("child")
        parent.add_child(child)
        tree.root.add_child(parent)
        
        tree.print_tree()
        captured = capsys.readouterr()
        assert "root" in captured.out
        assert "parent" in captured.out
        assert "child" in captured.out
    
    def test_get_leaves_at_level(self):
        """Тест получения листьев на заданном уровне"""
        tree = CategoriesTree.__new__(CategoriesTree)
        tree.root = Node("root")
        
        parent1 = Node("parent1")
        parent2 = Node("parent2")
        child1 = Node("child1")
        child2 = Node("child2")
        
        tree.root.add_child(parent1)
        tree.root.add_child(parent2)
        parent1.add_child(child1)
        parent2.add_child(child2)
        
        # Проверяем уровень 0 (корень)
        result = tree.get_leaves_at_level(0)
        assert result == ["root"]
        
        # Проверяем уровень 1 (родители)
        result = tree.get_leaves_at_level(1)
        assert "parent1" in result
        assert "parent2" in result
        
        # Проверяем уровень 2 (дети)
        result = tree.get_leaves_at_level(2)
        assert "child1" in result
        assert "child2" in result
    
    def test_node_by_names_sequence(self):
        """Тест поиска узла по последовательности имён"""
        tree = CategoriesTree.__new__(CategoriesTree)
        tree.nodes = {}
        tree.nodes_without_parent = {}
        tree.root = Node("root")
        
        parent = Node("parent")
        child = Node("child")
        parent.add_child(child)
        tree.root.add_child(parent)
        
        # Тест пустой последовательности
        assert tree.node_by_names_sequence([]) == tree.root
        
        # Тест поиска существующего узла
        result = tree.node_by_names_sequence(["parent"])
        assert result == parent
        
        # Тест поиска дочернего узла
        result = tree.node_by_names_sequence(["parent", "child"])
        assert result == child
        
        # Тест поиска несуществующего узла
        result = tree.node_by_names_sequence(["nonexistent"])
        assert result is None

# Тесты для класса Product
class TestProduct:
    def test_product_namedtuple(self):
        """Тест создания именованного кортежа Product"""
        product = Product(1, "test_product", "kg")
        assert product.id == 1
        assert product.name == "test_product"
        assert product.measurement_unit == "kg"

# Тесты для класса ProductWithPrice
class TestProductWithPrice:
    def test_init(self):
        """Тест инициализации ProductWithPrice"""
        product = ProductWithPrice(1, "test_product", "kg", [10.0, 20.0, 30.0])
        assert product.id == 1
        assert product.name == "test_product"
        assert product.measurement_unit == "kg"
        assert np.array_equal(product.prices, np.array([10.0, 20.0, 30.0]))
    
    def test_price_property(self):
        """Тест свойства price"""
        product = ProductWithPrice(1, "test_product", "kg", [10.0, 20.0, 30.0])
        assert product.price == 20.0  # медиана [10, 20, 30] = 20
        
        product = ProductWithPrice(1, "test_product", "kg", [10.0, 20.0])
        assert product.price == 15.0  # медиана [10, 20] = 15

# Тесты для других классов
class TestOtherClasses:
    def test_product_volume(self):
        """Тест для класса ProductVolume"""
        volume = ProductVolume(1, 10.0)
        assert volume.product_id == 1
        assert volume.quantity == 10.0
    
    def test_product_volume2(self):
        """Тест для класса ProductVolume2"""
        product = Product(1, "apple", "kg")
        volume = ProductVolume2(product, 10.0)
        assert volume.product == product
        assert volume.quantity == 10.0
    
    def test_product_volume_with_price(self):
        """Тест для класса ProductVolumeWithPrice"""
        product = ProductWithPrice(1, "apple", "kg", [10.0])
        volume = ProductVolumeWithPrice(product, 10.0)
        assert volume.product == product
        assert volume.quantity == 10.0

# Тесты для функций модуля
class TestModuleFunctions:
    def test_parse_add_product_message(self):
        """Тест функции parse_add_product_message"""
        text = "add apple kg"
        product = parse_add_product_message(text)
        assert product.id == -1
        assert product.name == "apple"
        assert product.measurement_unit == "kg"
        
        text = "add banana pieces"
        product = parse_add_product_message(text)
        assert product.id == -1
        assert product.name == "banana"
        assert product.measurement_unit == "pieces"
    
    @patch('product_storage.db.insert')
    def test_add_product(self, mock_insert):
        """Тест функции add_product"""
        add_product("Apple", "kg")
        mock_insert.assert_called_once_with("products", {"name": "apple", "measurement_unit": "kg"})
    
    @patch('product_storage.db.cursor')
    def test_get_products_in_storage(self, mock_cursor):
        """Тест функции get_products_in_storage"""
        mock_cursor.fetchall.return_value = [(1, 10.0), (2, 20.0)]
        
        # Тест без фильтрации по ID
        result = get_products_in_storage()
        assert len(result) == 2
        assert result[0] == ProductVolume(1, 10.0)
        assert result[1] == ProductVolume(2, 20.0)
        
        # Тест с фильтрацией по ID
        result = get_products_in_storage([1])
        assert len(result) == 1
        assert result[0] == ProductVolume(1, 10.0)
        
        # Тест пустого результата
        mock_cursor.fetchall.return_value = []
        result = get_products_in_storage()
        assert result == []
    
    @patch('product_storage.db.cursor')
    @patch('product_storage.get_product_by_id')
    def test_get_product_changes(self, mock_get_product, mock_cursor):
        """Тест функции get_product_changes"""
        mock_cursor.fetchall.return_value = [(1, 10.0, 101, '2023-01-01'), (2, 20.0, 102, '2023-01-02')]
        mock_get_product.side_effect = lambda pid: ProductWithPrice(pid, f"product_{pid}", "kg", [10.0])
        
        # Тест без фильтров
        result = get_product_changes()
        assert isinstance(result, defaultdict)
        assert '2023-01-01' in result
        assert '2023-01-02' in result
        assert 101 in result['2023-01-01']
        assert 102 in result['2023-01-02']
        
        # Тест с фильтрами
        result = get_product_changes(user_ids=[101], product_ids=[1], 
                                    from_date='2023-01-01', to_date='2023-01-01')
        mock_cursor.execute.assert_called()
    
    @patch('product_storage.db.cursor')
    def test_get_products_by_category(self, mock_cursor):
        """Тест функции get_products_by_category"""
        mock_cursor.fetchall.return_value = [(1, "apple", "kg"), (2, "banana", "pieces")]
        
        result = get_products_by_category("fruits")
        
        assert len(result) == 2
        assert result[0] == Product(1, "apple", "kg")
        assert result[1] == Product(2, "banana", "pieces")
        
        # Тест пустого результата
        mock_cursor.fetchall.return_value = []
        result = get_products_by_category("not_exist")
        assert result == []
    
    @patch('product_storage.db.cursor')
    @patch('product_storage.get_product_by_name')
    def test_get_product_in_storage_by_name(self, mock_get_product, mock_cursor):
        """Тест функции get_product_in_storage_by_name"""
        # Тест когда продукт найден
        mock_cursor.fetchone.return_value = (1, "apple", "kg", 10.0)
        
        result = get_product_in_storage_by_name("apple")
        assert result == ProductVolume(1, 10.0)
        
        # Тест когда продукта нет в storage, но он есть в products
        mock_cursor.fetchone.return_value = (1, "banana", "pieces", None)
        mock_get_product.return_value = ProductWithPrice(1, "banana", "pieces", [15.0])
        
        result = get_product_in_storage_by_name("banana")
        assert result == ProductVolume(1, 0)
        
        # Тест когда продукт не найден вообще
        mock_cursor.fetchone.return_value = None
        mock_get_product.return_value = None
        
        result = get_product_in_storage_by_name("unknown")
        assert result is None
    
    @patch('product_storage.db.cursor')
    def test_get_product_by_name(self, mock_cursor):
        """Тест функции get_product_by_name"""
        mock_cursor.fetchone.return_value = (1, "apple", "kg", "10.0,20.0")
        
        result = get_product_by_name("apple")
        
        assert result.id == 1
        assert result.name == "apple"
        assert result.measurement_unit == "kg"
        assert np.array_equal(result.prices, np.array([10.0, 20.0]))
        
        # Тест когда продукт не найден
        mock_cursor.fetchone.return_value = (None, None, None, None)
        result = get_product_by_name("unknown")
        assert result is None
    
    @patch('product_storage.db.cursor')
    def test_get_products(self, mock_cursor):
        """Тест функции get_products"""
        mock_cursor.fetchall.return_value = [
            (1, "apple", "kg", "10.0,20.0"),
            (2, "banana", "pieces", "5.0")
        ]
        
        result = get_products()
        
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "apple"
        assert result[1].id == 2
        assert result[1].name == "banana"
        
        # Тест пустого результата
        mock_cursor.fetchall.return_value = []
        result = get_products()
        assert result == []
    
    @patch('product_storage.db.cursor')
    def test_get_product_by_id(self, mock_cursor):
        """Тест функции get_product_by_id"""
        mock_cursor.fetchone.return_value = (1, "apple", "kg", "10.0,20.0")
        
        result = get_product_by_id(1)
        
        assert result.id == 1
        assert result.name == "apple"
        assert result.measurement_unit == "kg"
        assert np.array_equal(result.prices, np.array([10.0, 20.0]))
        
        # Тест когда продукт не найден
        mock_cursor.fetchone.return_value = None
        result = get_product_by_id(999)
        assert result is None
    
    @patch('product_storage.db.cursor')
    def test_get_product_by_id_v0(self, mock_cursor):
        """Тест функции get_product_by_id_v0"""
        mock_cursor.fetchone.return_value = (1, "apple", "kg", 10.0)
        
        result = get_product_by_id_v0(1)
        
        assert result.id == 1
        assert result.name == "apple"
        assert result.measurement_unit == "kg"
        
        # Тест когда продукт не найден
        mock_cursor.fetchone.return_value = None
        result = get_product_by_id_v0(999)
        assert result is None
    
    @patch('product_storage.get_product_in_storage_by_name')
    @patch('product_storage.db.insert')
    def test_increment(self, mock_insert, mock_get_product):
        """Тест функции increment"""
        mock_get_product.return_value = ProductVolume(1, 10.0)
        
        increment("apple", 5.0, 101)
        
        mock_get_product.assert_called_once_with("apple")
        mock_insert.assert_called_once_with("product_changes", 
                                          {"product_id": 1, "quantity": 5.0, "action_id": 101})
        
        # Тест когда продукт не найден
        mock_get_product.return_value = None
        mock_insert.reset_mock()
        
        increment("unknown", 5.0, 102)
        
        mock_get_product.assert_called_once_with("unknown")
        mock_insert.assert_not_called()
    
    @patch('product_storage.db.cursor')
    def test_get_product_changes_by_action_id(self, mock_cursor):
        """Тест функции get_product_changes_by_action_id"""
        # Подготовка мока для теста
        with patch('product_storage.ProductWithPrice') as mock_product_with_price:
            mock_instance = MagicMock()
            mock_product_with_price.return_value = mock_instance
            
            mock_cursor.fetchall.return_value = [(1, "apple", "kg", 10.0, 5.0)]
            
            result = get_product_changes_by_action_id(101)
            
            mock_cursor.execute.assert_called_once()
            assert len(result) == 1
            
            # Тест пустого результата
            mock_cursor.fetchall.return_value = []
            result = get_product_changes_by_action_id(999)
            assert result == []
    
    @patch('product_storage.new_action_get_id')
    @patch('product_storage.get_product_by_id')
    @patch('product_storage.increment')
    def test_increment_products(self, mock_increment, mock_get_product, mock_new_action):
        """Тест функции increment_products"""
        mock_new_action.return_value = 101
        product = ProductWithPrice(1, "apple", "kg", [10.0])
        mock_get_product.return_value = product
        
        increments = [ProductVolume(1, 5.0)]
        increment_products(increments, 1, "test_action", datetime.date.today())
        
        mock_new_action.assert_called_once()
        mock_get_product.assert_called_once_with(1)
        mock_increment.assert_called_once_with("apple", 5.0, 101)
    
    def test_volumes_cost_sum(self):
        """Тест функции volumes_cost_sum"""
        volumes = [
            ProductVolumeWithPrice(ProductWithPrice(1, "apple", "kg", [10.0]), 2.0),
            ProductVolumeWithPrice(ProductWithPrice(2, "banana", "pieces", [5.0]), 3.0)
        ]
        
        result = volumes_cost_sum(volumes)
        # 2.0 * 10.0 + 3.0 * 5.0 = 20.0 + 15.0 = 35.0
        assert result == 35.0
        
        # Тест с пустым списком
        assert volumes_cost_sum([]) == 0
    
    @patch('product_storage.get_product_by_name')
    @patch('product_storage.db.insert')
    def test_set_price(self, mock_insert, mock_get_product):
        """Тест функции set_price"""
        product = ProductWithPrice(1, "apple", "kg", [10.0])
        mock_get_product.return_value = product
        
        set_price("apple", 15.0)
        
        mock_get_product.assert_called_once_with("apple")
        mock_insert.assert_called_once_with("product_price", {"product_id": 1, "price": 15.0})
    
    def test_volumes_string(self):
        """Тест функции volumes_string"""
        volumes = [
            ProductVolumeWithPrice(ProductWithPrice(1, "apple", "kg", [10.0]), 2.0),
            ProductVolumeWithPrice(ProductWithPrice(2, "banana", "pieces", [5.0]), 3.0)
        ]
        
        result = volumes_string(volumes)
        expected = "\napple: 2.0 kg; 20.0 лари\nbanana: 3.0 pieces; 15.0 лари"
        assert result == expected
        
        # Тест с пустым списком
        assert volumes_string([]) == ""
    
    @patch('product_storage.db.cursor')
    def test_get_product_categories_v0(self, mock_cursor):
        """Тест функции get_product_categories_v0"""
        mock_cursor.fetchall.return_value = [("fruits",), ("vegetables",)]
        
        result, level = get_product_categories_v0()
        
        assert level == 1
        assert "fruits" in result
        assert "vegetables" in result
        
        # Тест с родительской категорией
        result, level = get_product_categories_v0(max_level=2, parent_category="fruits")
        mock_cursor.execute.assert_called()
        
        # Тест когда нет категорий на указанном уровне
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchall.side_effect = [[], [("fruits",), ("vegetables",)]]
        
        result, level = get_product_categories_v0(max_level=2)
        assert level == 1

    @patch('product_storage.PRODUCTS_TREE')
    def test_get_product_categories(self, mock_tree):
        """Тест функции get_product_categories"""
        # Настройка мока
        mock_node = MagicMock()
        mock_child1 = MagicMock()
        mock_child1.key = "child1"
        mock_child2 = MagicMock()
        mock_child2.key = "child2"
        mock_node.children = [mock_child1, mock_child2]
        mock_tree.node_by_names_sequence.return_value = mock_node
        
        # Тест с последовательностью имен
        result = get_product_categories(["parent"])
        
        mock_tree.node_by_names_sequence.assert_called_once_with(["parent"])
        assert "child1" in result
        assert "child2" in result
        
        # Тест с пустой последовательностью
        mock_root = MagicMock()
        mock_root_child = MagicMock()
        mock_root_child.key = "root_child"
        mock_root.children = [mock_root_child]
        mock_tree.root = mock_root
        mock_tree.node_by_names_sequence.return_value = None
        
        result = get_product_categories([])
        assert "root_child" in result
        
        # Тест когда узел не найден
        mock_tree.node_by_names_sequence.return_value = None
        
        result = get_product_categories(["nonexistent"])
        assert result == []

    @patch('product_storage.PRODUCTS_TREE_COOK')
    def test_get_product_categories_cook(self, mock_tree):
        """Тест функции get_product_categories_cook"""
        # Настройка мока
        mock_node = MagicMock()
        mock_child1 = MagicMock()
        mock_child1.key = "child1"
        mock_child2 = MagicMock()
        mock_child2.key = "child2"
        mock_node.children = [mock_child1, mock_child2]
        mock_tree.node_by_names_sequence.return_value = mock_node
        
        # Тест с последовательностью имен
        result = get_product_categories_cook(["parent"])
        
        mock_tree.node_by_names_sequence.assert_called_once_with(["parent"])
        assert "child1" in result
        assert "child2" in result
        
        # Тест с пустой последовательностью
        mock_root = MagicMock()
        mock_root_child = MagicMock()
        mock_root_child.key = "root_child"
        mock_root.children = [mock_root_child]
        mock_tree.root = mock_root
        mock_tree.node_by_names_sequence.return_value = None
        
        result = get_product_categories_cook([])
        assert "root_child" in result
        
        # Тест когда узел не найден
        mock_tree.node_by_names_sequence.return_value = None
        
        result = get_product_categories_cook(["nonexistent"])
        assert result == []

    @patch('product_storage.CATEGORIES_TREE_EXPENSES')
    def test_get_product_categories_expenses(self, mock_tree):
        """Тест функции get_product_categories_expenses"""
        # Настройка мока
        mock_node = MagicMock()
        mock_child1 = MagicMock()
        mock_child1.key = "child1"
        mock_child2 = MagicMock()
        mock_child2.key = "child2"
        mock_node.children = [mock_child1, mock_child2]
        mock_tree.node_by_names_sequence.return_value = mock_node
        
        # Тест с последовательностью имен
        result = get_product_categories_expenses(["parent"])
        
        mock_tree.node_by_names_sequence.assert_called_once_with(["parent"])
        assert "child1" in result
        assert "child2" in result
        
        # Тест с пустой последовательностью
        mock_root = MagicMock()
        mock_root_child = MagicMock()
        mock_root_child.key = "root_child"
        mock_root.children = [mock_root_child]
        mock_tree.root = mock_root
        mock_tree.node_by_names_sequence.return_value = None
        
        result = get_product_categories_expenses([])
        assert "root_child" in result
        
        # Тест когда узел не найден
        mock_tree.node_by_names_sequence.return_value = None
        
        result = get_product_categories_expenses(["nonexistent"])
        assert result == [] 