import os

import sqlite3
from typing import Dict, List, Tuple


class PosterStorage:
    """Singleton"""
    _instance = None

    def __new__(cls, path=None):
        if not cls._instance:
            cls._instance = super(PosterStorage, cls).__new__(cls)
        return cls._instance

    def __init__(self, path=None):
        pass

    @property
    def id_name_dict(self):
        return {}

    def get_storage(self):
        pass

    def get_ingredien_by_id(self, ingredient_id: int):
        pass
