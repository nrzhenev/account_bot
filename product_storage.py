""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
from collections import defaultdict
from typing import NamedTuple, Optional, List, Tuple

import regex as re
import numpy as np

from db_modules.db import DataBase
from pkg import new_action_get_id, ActionType, db

db = DataBase()


class Node:
    def __init__(self, key):
        self.key = key
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def __repr__(self):
        return self.key

    def print(self, spaces=0):
        print(" " * spaces + self.key)
        for child in self.children:
            child.print(spaces + 1)


class CategoriesTree:
    # _INSTANCE = None
    # _initialized = False

    # def __new__(cls):
    #     if not cls._INSTANCE:
    #         cls._INSTANCE = super(ProductCategoriesTree, cls).__new__(cls)
    #     return cls._INSTANCE

    def __init__(self, category_type: str, data_base=db):
        self.nodes = {}
        self.nodes_without_parent = {}
        self.root = Node("root")

        cursor = data_base.cursor
        # cursor.execute("select id, name, measurement_unit, quantity from product_storage")
        cursor.execute(
            "select cl.target, cl.category from category_links cl join categories c on cl.category = c.category where c.type = ?", (category_type,))
        rows = cursor.fetchall()
        self.build_tree(rows)

    def add_edge(self, parent_key, child_key):
        parent_node = self.nodes.get(parent_key)
        if parent_node is None:
            parent_node = self.nodes_without_parent.get(parent_key)
        if parent_node is None:
            parent_node = Node(parent_key)
            self.nodes_without_parent[parent_key] = parent_node

        child_node = self.nodes.get(child_key)
        if not child_node:
            child_node = self.nodes_without_parent.get(child_key)
            if child_node is not None:
                self.nodes[child_node] = self.nodes_without_parent.pop(child_key)

        if child_node is None:
            child_node = Node(child_key)
            self.nodes[child_key] = child_node
        parent_node.add_child(child_node)

    def build_tree(self, edges):
        for child, parent in edges:
            self.add_edge(parent, child)
        for key, node in self.nodes_without_parent.items():
            self.root.add_child(node)

    def print_tree(self, node=None, level=0):
        if node is None:
            node = self.root
        print(' ' * level * 4 + str(node.key))
        for child in node.children:
            self.print_tree(child, level + 1)

    def get_leaves_at_level(self, desired_level, node=None, current_level=0):
        result = []
        if node is None:
            node = self.root
        if node is not None:
            if current_level == desired_level:
                result.append(node.key)
            for child in node.children:
                result += self.get_leaves_at_level(desired_level, child, current_level + 1)
        return result

    def node_by_names_sequence(self, names_sequence):
        if len(names_sequence) == 0:
            return self.root
        return self._node_by_names_sequence(names_sequence, self.root)

    def _node_by_names_sequence(self, names_sequence, initial_node):
        if len(names_sequence) < 1:
            return

        if len(names_sequence) == 1:
            for child in initial_node.children:
                if child.key == names_sequence[0]:
                    return child
            return

        for child in initial_node.children:
            if child.key == names_sequence[0]:
                return self._node_by_names_sequence(names_sequence[1:], child)


PRODUCTS_TREE = CategoriesTree("product_category")
PRODUCTS_TREE_COOK = CategoriesTree("product_category_cook")
CATEGORIES_TREE_EXPENSES = CategoriesTree("expenses_category")


class Product(NamedTuple):
    id: int
    name: str
    measurement_unit: str


class ProductWithPrice:
    def __init__(self, id: int, name: str, measurement_unit: str, prices: List[float]):
        self.id = id
        self.name = name
        self.measurement_unit = measurement_unit
        self.prices = np.array(prices)

    @property
    def price(self):
        return np.median(self.prices)


class ProductVolume(NamedTuple):
    product_id: int
    quantity: float


class ProductVolume2(NamedTuple):
    product: Product
    quantity: float


class ProductVolumeWithPrice(NamedTuple):
    product: ProductWithPrice
    quantity: float


def parse_add_product_message(text: str) -> Product:
    words = re.findall("\S+", text)[1:]
    return Product(-1, words[-2], words[-1])


def increments_from_text(text: str):
    pass
    # """Парсит текст пришедшего сообщения о новом расходе."""
    # regexp_result = re.findall(r"[\d]+ [^\d,.]+", text)
    # result_messages = []
    #
    # for result in regexp_result:
    #     amount = re.search("\d+", result).group()
    #     category_text = re.search("(?<=\d+\s).+", result).group()
    #     amount = int(amount.strip(" ,."))
    #     category_text = category_text.strip(" ,.")
    #     result_messages.append(ProductVolume(category_text, amount))
    # return result_messages


def increments_from_text0(text: str):
    pass
    # """Парсит текст пришедшего сообщения о новом расходе."""
    # regexp_result = re.findall(r"[\d]+ [^\d,]+", text)
    # result_messages = []
    #
    # for result in regexp_result:
    #     amount = re.search("\d+", result).group()
    #     category_text = re.search("(?<=\d+\s).+", result).group()
    #     amount = float(amount.strip(" ,"))
    #     name = category_text.strip(" ,")
    #     increment(name, amount)
    #     result_messages.append(ProductVolume(name, amount))
    # return result_messages


def add_product(product_name: str, measurement_unit: str, data_base=db):
    product_name = product_name.lower()
    data_base.insert("products",
              {"name": product_name, "measurement_unit": measurement_unit})


def get_products_in_storage(ids: Optional[List[int]]=None, data_base=db) -> List[ProductVolume]:
    cursor = data_base.cursor
    #cursor.execute("select id, name, measurement_unit, quantity from product_storage")
    cursor.execute("select p.id, SUM(pc.quantity) from products p join product_changes pc on p.id = pc.product_id group by p.id")
    rows = cursor.fetchall()
    if not rows:
        return []

    result = []
    for row in rows:
        if ids and row[0] not in ids:
            continue
        result.append(ProductVolume(*row))
    return result


def get_product_changes(user_ids: List[int]=None,
                        product_ids: List[int]=None,
                        from_date: datetime.date=None,
                        to_date: datetime.date=None,
                        data_base=db) -> dict:
    cursor = data_base.cursor
    result = defaultdict(lambda: defaultdict(list))
    # cursor.execute("select id, name, measurement_unit, quantity from product_storage")
    user_ids_condition = ""
    product_ids_condition = ""
    date_from_condition = ""
    date_to_condition = ""

    variables = []
    if user_ids:
        variables += user_ids
        user_ids_condition = f"user_id in ({', '.join(['?' for _ in user_ids])})"
    if product_ids:
        variables += product_ids
        product_ids_condition = f"product_id in ({', '.join(['?' for _ in product_ids])})"
    if from_date:
        variables.append(from_date)
        date_from_condition = f"created >= ? "
    if to_date:
        variables.append(to_date)
        date_to_condition = f"created <= ?"

    conditions_string = ' AND '.join([cond for cond in [user_ids_condition,
                                                        product_ids_condition,
                                                        date_from_condition,
                                                        date_to_condition] if cond])

    main_query = (f"select product_id, quantity, user_id," +
                  f" created from product_changes pc join actions a on pc.action_id = a.action_id")
    if variables:
        cursor.execute(f"{main_query} WHERE {conditions_string}", variables)
    else:
        cursor.execute(main_query)
    rows = cursor.fetchall()
    #result = []
    for row in rows:
        product_id, quantity, user_id, created_date = row
        product = get_product_by_id(product_id, data_base)
        result[created_date][user_id].append(ProductVolumeWithPrice(product, quantity))
    return result


def get_products_by_category(category: str, data_base=db) -> List[Product]:
    cursor = data_base.cursor
    cursor.execute("select p.id, p.name, p.measurement_unit from "
                   "products p join (select * from categories c join category_links cl on c.category = cl.category) pc on p.name = pc.target where pc.type = 'product_category' and pc.category = ?", (category,))
    rows = cursor.fetchall()
    if not rows:
        return []

    result = []
    for row in rows:
        result.append(Product(row[0], row[1], row[2]))
    return result


def get_product_in_storage_by_name(product_name: str, data_base=db) -> Optional[ProductVolume]:
    cursor = data_base.cursor
    cursor.execute("select p.id, p.name, p.measurement_unit, SUM(pc.quantity) from products p join product_changes pc on p.id = pc.product_id where p.name = (?)",
                   (product_name,))
    result = cursor.fetchone()
    if not result or not result[3]:
        product = get_product_by_name(product_name, data_base)
        if not product:
            return
        return ProductVolume(product.id, 0)
    return ProductVolume(result[0], result[3])


def get_product_by_name(product_name: str, data_base=db) -> Optional[ProductWithPrice]:
    cursor = data_base.cursor
    cursor.execute("select p.id, p.name, p.measurement_unit, IFNULL(GROUP_CONCAT(pp.price), '0') as prices from products p LEFT JOIN product_price pp on p.id = pp.product_id where p.name = (?)",
                   (product_name,))
    result = cursor.fetchone()
    id, name, measurement_unit, prices = result
    if not (id and name):
        return
    prices = [float(price) for price in result[3].split(",")]
    return ProductWithPrice(*result[:-1], prices)


def get_products(data_base=db) -> List[ProductWithPrice]:
    cursor = data_base.cursor
    cursor.execute("select p.id, p.name, p.measurement_unit, IFNULL(GROUP_CONCAT(pp.price), '0') from products p LEFT JOIN product_price pp ON p.id = pp.product_id GROUP BY p.id")
    rows = cursor.fetchall()
    if not rows:
        return []

    return [ProductWithPrice(*row[:3], [float(price) for price in row[3].split(",")]) for row in rows]


def get_product_by_id(product_id: int, data_base=db) -> Optional[ProductWithPrice]:
    cursor = data_base.cursor
    cursor.execute("select p.id, p.name, p.measurement_unit, GROUP_CONCAT(pp.price) from products p JOIN product_price pp ON p.id = pp.product_id where p.id = (?) group by p.id",
                   (product_id,))
    result = cursor.fetchone()
    if not result:
        return
    prices_string = result[-1]
    prices = [float(price) for price in prices_string.split(",")]
    return ProductWithPrice(*result[:-1], prices)


def get_product_by_id_v0(product_id: int, data_base=db) -> Optional[Product]:
    cursor = data_base.cursor
    cursor.execute("select p.id, p.name, p.measurement_unit, SUM(pc.quantity) from products p join product_changes pc on p.id = pc.product_id where p.id = (?) group by p.id",
                   (product_id,))
    result = cursor.fetchone()
    if not result:
        return
    return Product(*result)


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


def volumes_cost_sum(volumes: List[ProductVolumeWithPrice]) -> float:
    sum_price = 0
    for vol in volumes:
        sum_price += vol.quantity * vol.product.price
    return sum_price


def set_price(product_name: str, new_price: float, data_base=db):
    product = get_product_by_name(product_name, data_base)
    data_base.insert("product_price", {"product_id": product.id, "price": new_price})


def volumes_string(volumes: List[ProductVolumeWithPrice]) -> str:
    result = ""
    if not volumes:
        return result
    # if isinstance(volumes[0], ProductVolume):
    #     for vol in volumes:
    #         product = get_product_by_id(vol.product_id)
    #         result += "\n" + f"{product.name}: {vol.quantity} {product.measurement_unit}"
    # elif isinstance(volumes[0], ProductVolume2):
    #     for vol in volumes:
    #         product = vol.product
    #         result += "\n" + f"{product.name}: {vol.quantity} {product.measurement_unit}"
    for vol in volumes:
        product = vol.product
        result += "\n" + f"{product.name}: {vol.quantity} {product.measurement_unit}; {vol.product.price*vol.quantity} лари"
    return result


def get_product_categories_v0(max_level: int=1,
                              parent_category: Optional[str]=None,
                              data_base=db) -> Tuple[List[str], int]:
    result = None
    while max_level != 0 and not result:
        cursor = data_base.cursor
        if parent_category and max_level != 1:
            cursor.execute(
                "select distinct cl.target from category_links cl join categories c on cl.category=c.category where type = 'product_category' and cl.category = ? and cl.hierarchy_level = ?",
                (parent_category, max_level,))
        else:
            cursor.execute(
                "select distinct cl.category from category_links cl join categories c on cl.category=c.category where type = 'product_category' and hierarchy_level = ?", (max_level,))

        result = cursor.fetchall()
        if result and result[0][0]:
            return [row[0] for row in result], max_level
        max_level -= 1


def get_product_categories(names_sequence: List[str]) -> List[str]:
    tree = PRODUCTS_TREE
    node = tree.node_by_names_sequence(names_sequence)
    if not names_sequence:
        return [c.key for c in tree.root.children]
    if not node:
        return []
    return [c.key for c in node.children]


def get_product_categories_cook(names_sequence: List[str]) -> List[str]:
    tree = PRODUCTS_TREE
    node = tree.node_by_names_sequence(names_sequence)
    if not names_sequence:
        return [c.key for c in tree.root.children]
    if not node:
        return []
    return [c.key for c in node.children]


def get_product_categories_expenses(names_sequence: List[str]) -> List[str]:
    tree = CATEGORIES_TREE_EXPENSES
    node = tree.node_by_names_sequence(names_sequence)
    if not names_sequence:
        return [c.key for c in tree.root.children]
    if not node:
        return []
    return [c.key for c in node.children]
