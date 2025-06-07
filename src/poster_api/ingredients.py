from datetime import datetime

import requests
from typing import List, NamedTuple

from credentials import POS
from src.poster_api.pkg import pos_request


def get_ingridients():
    response = pos_request(f"menu.getIngredients")
    result = []
    for product_dict in response:
        result.append({"name": product_dict["ingredient_name"],
                       "id": product_dict["ingredient_id"],
                       "unit": product_dict["ingredient_unit"]})
    return result


params = {
    "token": POS
}
url = "https://joinposter.com/api/storage.createSupply"


class Supply(NamedTuple):
    id: int
    num: float
    unit_price: float


def send_shipment(ingredients: List[Supply]):
    payload = {
        "supply": {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "supplier_id": "4",
            "storage_id": "1",
            "packing": "1"
        },
        "ingredient": [{
                "id": str(supply.id),
                "type": "4",
                "num": str(supply.num),
                "sum": str(supply.unit_price)
            } for supply in ingredients]
    }
    response = requests.post(url, params=params, json=payload)
    if response.status_code != 200:
        raise ValueError("Could not send shipment")
