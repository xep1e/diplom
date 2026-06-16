import requests

TOKEN = "f9LHodD0cOIbSEdo_jRt895t4f8cphEN9gemDGgTnzGFStVFym7fWqymel_y-80g3SPqh-727dhM20R7IpiA"

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

payload = {
    "url": "https://ee3e-78-17-31-243.ngrok-free.app/max/webhook",

    # чтобы получать события
    "update_types": [
        "message_created",
        "bot_started"
    ]
}

r = requests.post(
    "https://platform-api.max.ru/subscriptions",
    headers=headers,
    json=payload
)

print(r.status_code)
print(r.text)