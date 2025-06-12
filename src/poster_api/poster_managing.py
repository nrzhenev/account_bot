import json
from typing import List

import requests

from credentials import POS


def _poster_request(url, **kwargs):
    kwargs["token"] = POS
    res = f"https://joinposter.com/api/{url}?{'&'.join([f'{key}={value}' for key, value in kwargs.items()])}"
    response = requests.get(res)
    if response.status_code != 200:
        return []
    return json.loads(response.text)['response']


def _poster_request_with_json(method, addition):
    url = f"https://joinposter.com/api/{method}?token={POS}"
    response = requests.post(url, json=addition)
    if response.status_code != 200:
        return []
    return json.loads(response.text)


def dish_ids_containing_ingredient(ingredient_id):
    preparations = _poster_request("menu.getPrepacks")

    def has_id(preparation):
        return any(str(i["ingredient_id"]) == str(ingredient_id) for i in preparation["ingredients"])

    return [dish["product_id"] for dish in filter(lambda p: has_id(p), preparations)]


def products_containing_ingredient(ingredient_id: int):
    possible_ingredients_ids = [ingredient_id] + dish_ids_containing_ingredient(ingredient_id)
    possible_ingredients_ids_str = set([str(ing) for ing in possible_ingredients_ids])
    products = _poster_request(f"menu.getProducts")

    def has_any_id(product):
        product_ingredients_ids = set([str(ingredient["ingredient_id"]) for ingredient in product["ingredients"]])
        return bool(possible_ingredients_ids_str.intersection(product_ingredients_ids))

    complex_products = filter(lambda p: p.get("ingredients"), products)
    target_products = filter(lambda p: has_any_id(p), complex_products)
    return list(target_products)


def turn_off_products(target_product_ids: List[str]):
    for product_id in target_product_ids:
        addition = {"dish_id": product_id, "visible": {"1": 0}}
        _poster_request_with_json("menu.updateDish", addition)
