import os
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Webhook from .env
TOKEN_INFORU = os.getenv("TOKEN_INFORU")

# Test numbers (you can add more later)
dids = [
    "0778066666"
]

# Build payload exactly like app.py
payload = {
    "dids": dids,
    "numbers": ", ".join(dids),
    "count": len(dids)
}

print("\n==== TEST WEBHOOK ====")
print("Webhook URL:", TOKEN_INFORU)
print("Numbers being sent:", dids)
print("Payload:", payload)
print("======================\n")

try:

    response = requests.post(
        TOKEN_INFORU,
        json=payload,
        timeout=20
    )

    print("Status Code:", response.status_code)

    try:
        print("\nResponse JSON:")
        print(response.json())
    except:
        print("\nRaw Response:")
        print(response.text)

except Exception as e:
    print("Error:", str(e))