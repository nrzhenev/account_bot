""" Работа с расходами — их добавление, удаление, статистики"""
from typing import NamedTuple, Optional, Dict

import regex as re

from datetime import datetime
from typing import List

import aiohttp

from credentials import POSTER_TOKEN


async def read(command: str):
    url = f"https://joinposter.com/api/{command}?token={POSTER_TOKEN}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def write(command: str, data, headers=None):
    url = f"https://joinposter.com/api/{command}?token={POSTER_TOKEN}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()


class Product(NamedTuple):
    product_id: int
    product_name: str
    measurement_unit: str
    price: float
    quantity: float


class ProductIncrement(NamedTuple):
    product_id: int
    quantity_difference: float


class ProductWriteOff(NamedTuple):
    increment: ProductIncrement
    reason: str


class PosterStorage:
    """Singleton"""
    _instance = None

    def __new__(cls, path=None):
        if not cls._instance:
            cls._instance = super(PosterStorage, cls).__new__(cls)
            cls._instance._product_by_name = {}
        return cls._instance

    def __init__(self, path=None):
        if not hasattr(self, "_product_by_id"):
            self._product_by_id: Dict[int, Product] = {}
        #self._product_by_name: Dict[str, Product] = {}

    async def async_init(self):
        await self.get_products()

    async def product_by_id(self, product_id: int) -> Product:
        return self._product_by_id.get(product_id)

    async def product_by_name(self, product_name: str) -> Product:
        return self._product_by_name.get(product_name)

    async def get_products(self, from_index: Optional[int]=None, to_index: Optional[int]=None) -> List[Product]:
        answer = await read("storage.getStorageLeftovers")
        response = answer["response"]
        result = []
        for row in response:
            pid = int(row["ingredient_id"])
            name = row["ingredient_name"]
            quantity = float(row["ingredient_left"])
            unit = row["ingredient_unit"]
            price = float(row["prime_cost_netto"])/100
            product = Product(pid, name, unit, price, quantity)
            result.append(product)
            self._product_by_id[pid] = product
            self._product_by_name[name] = product
        result = sorted(result, key=lambda x: x.id)
        if to_index is not None:
            to_index += 1
        result_slice = slice(from_index, to_index, 1)
        return result[result_slice]

    async def get_name_id_dict(self) -> dict:
        result = {}
        for id, product in self._product_by_id:
            result[product.name] = id
        return result

    async def increment_products(self, increments: List[ProductIncrement], date: datetime=datetime.now()):
        supply = {
            "supply": {
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "supplier_id": "4",
                "storage_id": "1",
                "packing": "1"
            },

            "ingredient": [{
                "id": str(inc.product_id),
                "type": "4",
                "num": str(inc.quantity_difference),
                "sum": str(self._product_by_id[inc.product_id].price)
            } for inc in increments]
        }
        return await write(f"storage.createSupply", supply)

    async def write_off(self, write_offs: List[ProductWriteOff], date: datetime=datetime.now()):
        supply = {
            "write_off": {
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "storage_id": "1"
            },
            "ingredient": [{
                "id": str(write_off.increment.product_id),
                "type": "4",
                "weight": str(write_off.increment.quantity_difference),
                "reason": write_off.reason
            } for write_off in write_offs]
        }
        return await write(f"storage.createWriteOff", supply)


def parse_add_product_message(text: str) -> Product:
    words = re.findall("\S+", text)[1:]
    return Product(-1, words[-2], words[-1], 0)


def increments_from_text(text: str) -> List[ProductIncrement]:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.findall(r"[\d]+ [^\d,.]+", text)
    result_messages = []

    for result in regexp_result:
        amount = re.search("\d+", result).group()
        category_text = re.search("(?<=\d+\s).+", result).group()
        amount = int(amount.strip(" ,."))
        category_text = category_text.strip(" ,.")
        result_messages.append(ProductIncrement(category_text, amount))
    return result_messages


async def quantity_report():
    ps = PosterStorage()
    products = await ps.get_products()
    result = ""
    for product in products:
        result += f"\n{product.product_name}: {product.quantity} {product.measurement_unit}"
    return result


# def quantity_report() -> str:
#     products = get_products()
#     products = [product for product in products if product.quantity]
#     return "Склад:\n" + "\n".join([f"{pr.name}: {pr.quantity} {pr.measurement_unit}" for pr in products])
