from typing import NamedTuple, List

import numpy as np


class Product(NamedTuple):
    id: int
    name: str
    measurement_unit: str


class ProductWithPrice:
    def __init__(self, id: int, name: str, measurement_unit: str, prices: List[float]):
        self.id = id
        self.name = name
        self.measurement_unit = measurement_unit
        self.prices = prices

    @property
    def price(self):
        return np.median(np.ndarray(self.prices))


class PosterIngredient:
    def __init__(self,
                 id: int,
                 poster_id: int,
                 name: str,
                 category: str,
                 unit: str,
                 price: float):
        self.id = int(id)
        self.poster_id = int(poster_id)
        self.name = name
        self.category= category
        self._unit = unit
        self.price = float(price) if price else 0

    @property
    def unit(self):
        UNIT_TRANSLATION = {"p": "штук", "kg": "кг", "g": "грамм", "l": "литров"}
        return UNIT_TRANSLATION.get(self._unit, self._unit)


class ProductVolume(NamedTuple):
    product_id: int
    quantity: float


class ProductVolumeWithPrice(NamedTuple):
    product: ProductWithPrice
    quantity: float
