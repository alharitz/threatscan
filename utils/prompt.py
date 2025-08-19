import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN")
MODEL_ID = "@cf/mistral/mistral-7b-instruct-v0.1"

# Choose one of the following payloads:

# 1. Simple prompt mode:
payload = {
    "prompt": "What is the best asset to be invested right now?"
}

# 2. Chat mode with system/user roles:
# payload = {
#     "messages": [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user",   "content": "Explain PEP 8 guidelines in Python."}
#     ]
# }

response = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL_ID}",
    headers={
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    },
    json=payload
)

if response.ok:
    data = response.json()
    # The generated text is under data["result"]["response"]
    print(data["result"]["response"])
else:
    print(f"Error {response.status_code}: {response.text}")
