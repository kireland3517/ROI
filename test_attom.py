import os

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("ATTOM_API_KEY", "")

url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/sale/snapshot"

params = {
    "postalcode": "29229",
    "startsalesearchdate": "2024-01-01",
    "endsalesearchdate": "2024-12-31",
}

headers = {
    "apikey": API_KEY,
    "accept": "application/json",
}

response = requests.get(url, headers=headers, params=params)

print("Status code:", response.status_code)
print("Response:", response.json())
