from typing import List
from db_modules.db import DataBase


db = DataBase()


def add_expenses_category_link(category_link: List[str]):
    for target, category in zip(category_link[:-1], category_link[1:]):
        db.insert("category_links", {"target": target, "category": category})

    for link in category_link:
        db.insert("categories", {"category": link, "type": "expenses_category"})