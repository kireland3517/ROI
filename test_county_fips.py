import os

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("ATTOM_API_KEY", "")

# Test 1: county parameter (user's original test)
print("=== Test: county=45045 ===")
response = requests.get(
    "https://api.gateway.attomdata.com/propertyapi/v1.0.0/sale/snapshot",
    headers={"apikey": API_KEY, "accept": "application/json"},
    params={
        "county": "45045",
        "startsalesearchdate": "2024-01-01",
        "endsalesearchdate": "2024-12-31",
        "pagesize": 10,
    },
)
print("Status:", response.status_code)
print(response.json())

# Test 2: fips parameter (correct parameter name)
print("\n=== Test: fips=45045 ===")
response2 = requests.get(
    "https://api.gateway.attomdata.com/propertyapi/v1.0.0/sale/snapshot",
    headers={"apikey": API_KEY, "accept": "application/json"},
    params={
        "fips": "45045",
        "startsalesearchdate": "2024-01-01",
        "endsalesearchdate": "2024-12-31",
        "pagesize": 3,
    },
)
data = response2.json()
print("Status:", response2.status_code)
print("Message:", data.get("status", {}).get("msg"))
print("Total:", data.get("status", {}).get("total"))
for p in data.get("property", []):
    addr = p.get("address", {})
    ident = p.get("identifier", {})
    sale = p.get("sale", {}).get("amount", {})
    print(f"  fips={ident.get('fips')} | {addr.get('oneLine')} | sale={sale.get('saleamt')}")
