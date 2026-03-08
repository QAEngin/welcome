import os
import requests
from dotenv import load_dotenv

load_dotenv()

SMS_URL = os.getenv("SMSURL")
SMS_TOKEN = os.getenv("SMSTOKEN")

params = {
    "TYPE": "SMS",
    "environment_name": "testdomain",
    "vml[0][caller_id_number]": "NIRR",
    "vml[0][number]": "077806661",
    "vml[0][template]": "TEXT Test"
}

headers = {
    "Basic": SMS_TOKEN
}

try:
    print("Sending SMS API request...\n")

    response = requests.post(
        SMS_URL,
        headers=headers,
        data=params,
        timeout=30
    )

    print("Status Code:", response.status_code)

    try:
        print("\nResponse JSON:")
        print(response.json())
    except Exception:
        print("\nRaw Response:")
        print(response.text)

except Exception as e:
    print("Error:", str(e))