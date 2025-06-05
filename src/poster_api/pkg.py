import json

import requests

from credentials import POS

def pos_request(url, **kwargs):
    kwargs["token"] = POS
    res = f"https://joinposter.com/api/{url}?{'&'.join([f'{key}={value}' for key, value in kwargs.items()])}"
    response = requests.get(res)
    if response.status_code != 200:
        return []
    return json.loads(response.text)['response']
