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


class ProductVolume(NamedTuple):
    product_id: int
    quantity: float


class ProductVolumeWithPrice(NamedTuple):
    product: ProductWithPrice
    quantity: float
