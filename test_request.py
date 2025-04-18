import requests

api_key = "defab562-f9b9-4ec2-a1e1-5c82ecf8f3f6"

headers = {
    "X-API-Key": api_key
}

url = "https://api.ember-energy.org/v1/electricity-generation/yearly?entity_code=CHN&is_aggregate_series=false&start_date=2000"

print("Request headers:", headers)
response = requests.get(url, headers=headers)

print("Status code:", response.status_code)
print("Text:", response.text)