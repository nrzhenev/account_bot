from typing import List

import aiohttp
import asyncio
from datetime import datetime

from credentials import POSTER_TOKEN
from poster_storage import PosterStorage, ProductIncrement


INGREDIENTS_IDS = {'Absolut Vodka': '55',
                   'Angostura': '56',
                   'Aperol': '47',
                   'Bacardi': '43',
                   'Baileys': '51',
                   'Ballantines': '42',
                   'Buga Энергетик': '65',
                   'Campari': '46',
                   'Captain Morgan': '50',
                   'Coca cola': '68',
                   'Disaronno': '67',
                   'Estrella beer': '86',
                   'Guinness': '76',
                   'Hougharden': '83',
                   'Jagermeister': '48',
                   'Jako': '41',
                   'Jameson': '44',
                   'Kahula': '52',
                   'Kayaki Пиво': '73',
                   'Mariti Bianco': '53',
                   'Maritini Rosso': '54',
                   'Mtis вода 0.5': '70',
                   'Nabeglavi 0.5': '71',
                   'Schwepps': '60',
                   'Sierra': '45',
                   'Tripplesec': '66',
                   'Авокадо': '21',
                   'Апельсин': '33',
                   'банан': '80',
                   'Васаби': '26',
                   'Вода обычная': '39',
                   'Икра Лосося': '34',
                   'Икра Тобико': '30',
                   'Имбирь': '36',
                   'киви': '82',
                   'клубника': '81',
                   'Креветка': '29',
                   'Кунжут': '20',
                   'Лаймовый сок': '58',
                   'Лимонный сок': '57',
                   'Листья салата': '32',
                   'Лосось другой': '84',
                   'Лосось маковый': '85',
                   'Лосось ролловый': '18',
                   'Лосось хороший': '87',
                   'Манго': '31',
                   'Мирин': '37',
                   'молоко': '75',
                   'Мороженое': '74',
                   'Нори': '27',
                   'Огурец': '22',
                   'Пиво Каяки': '49',
                   'Рис': '19',
                   'Снежный краб': '40',
                   'Соевый соус': '35',
                   'Сыр': '28',
                   'Тунец': '23',
                   'Угорь': '24',
                   'Уксус': '38',
                   'Энергетик': '59'}

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def send_post_request(url, data, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            return await response.json()


class Ingredient:
    def __init__(self, ingredient_id: int, num: int, sum: int):
        self.id = ingredient_id,
        self.num = num
        self.sum = sum

    @property
    def dict_format(self):
        return {
                "id": self.id,
                "type": "4",
                "num": self.num,
                "sum": self.sum
            }


async def shipment(ingredients: List[Ingredient],
                   date: datetime):
    supply = {
        "supply": {
            "date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "supplier_id": "4",
            "storage_id": "1",
            "packing": "1"
        },
        "ingredient": [ingredient.dict_format for ingredient in ingredients]
    }
    return await send_post_request(f"https://joinposter.com/api/storage.createSupply?token={POSTER_TOKEN}",
                                   supply)


async def read(command: str, **kwargs):
    token = kwargs["token"]
    params = [(f"token={token}")] + [f"{key}={value}" for key, value in kwargs.items() if key != "token"]
    query = "&".join(params)
    url = f"https://joinposter.com/api/{command}?{query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def write(command: str, data, **kwargs):
    token = kwargs["token"]
    params = [(f"token={token}")] + [f"{key}={value}" for key, value in kwargs.items() if key != "token"]
    query = "&".join(params)
    url = f"https://joinposter.com/api/{command}?{query}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            return await response.json()


async def storage():
    result = await read("storage.getStorageLeftovers", token=POSTER_TOKEN)
    result = result["response"]
    return result
    return [{"ingredient_id": i["ingredient_id"], "ingredient_name": i["ingredient_name"]} for i in result]


async def storage_ids():
    ingredients = await storage()
    result = {i["ingredient_name"]: i["ingredient_id"] for i in ingredients}
    return result

#
# # Проверка успешности запроса
# if response.status_code == 200:
#     # Распечатка ответа в формате JSON
#     print(response.json())
# else:
#     print(f'Ошибка {response.status_code}: {response.text}')
#
# supply = [
#     "supply" => [
#         "supply_id"     => "51",
#         "supplier_id"   => "1",
#         "storage_id"    => "1",
#         "date"          => date("Y-m-d H:i:s"),
#     ],
#     "ingredient" => [
#         [
#             "id"        => "138",
#             "type"      => "1",
#             "num"       => "3",
#             "sum"       => "6",
#         ]
#     ]
# ];
#
# def add_product(api_key, product_data):
#     endpoint = 'YOUR_ENDPOINT'
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {api_key}'
#     }
#
#     # Отправка POST-запроса для добавления продукта
#     response = requests.post(f'{endpoint}/products', json=product_data, headers=headers)
#
#     # Проверка успешности запроса
#     if response.status_code == 200:
#         print('Продукт успешно добавлен!')
#     else:
#         print(f'Ошибка {response.status_code}: {response.text}')
#
# # Пример данных продукта (замените на свои данные)
# product_data = {
#     "name": "Название продукта",
#     "price": 10.99,
#     "category": "Еда",
#     "inventory": 100
# }
#
# # Замените 'YOUR_API_KEY' на ваш ключ API Poster POS
# api_key = 'YOUR_API_KEY'
#
# # Вызов функции для добавления продукта
# add_product(api_key, product_data)


async def main():
    increments = [ProductIncrement(27, 3000)]
    date = datetime(2024, 1, 7)

    ps = PosterStorage()
    await ps.async_init()
    #result = await ps.increment_products(increments, date)
    res = await ps.get_products()
    print(1)


if __name__ == "__main__":
    result = asyncio.run(main())