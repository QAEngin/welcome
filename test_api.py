import requests

# API URL
url = "https://cloud.voipappz.io/api/schemas"

# Headers
headers = {
    "Authorization": "Basic bmltYnVzLWFwaUBnbWFpbC5jb206SzRaLXJfdw==",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Payload (same structure as Postman)
payload = {
    "type": "sms",
    "environment_name": "Zuratest1",
    "vml[0][caller_id_number]": "ZuraSMS",
    "vml[0][number]": "077888889",
    "vml[0][template]": "test"
}

try:
    response = requests.post(url, headers=headers, data=payload, timeout=30)

    print("Status Code:", response.status_code)
    print("-------------")

    # try JSON
    try:
        print("JSON Response:")
        print(response.json())
    except:
        print("Raw Response:")
        print(response.text)

except Exception as e:
    print("Request Error:", e)