import requests

def set_user_allowed_senders():
    # API Configuration
    url = "https://ws.interfax.net/admin.asmx"
    
    # Headers required by the SOAP 1.1 protocol
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://interfax.net/Admin/SetUserTxProperties"
    }

    # Your specific test data
    admin_user = "nimbusip"
    admin_pass = "e8nkQxYmRGAq"
    target_user = "fax2mail"
    new_email = "zura12345@gmail.com"

    # The SOAP XML Payload
    # Note: Using comma-separated values for AllowedSenders as per documentation.
    xml_payload = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SetUserTxProperties xmlns="http://interfax.net/Admin">
      <Username>{admin_user}</Username>
      <Password>{admin_pass}</Password>
      <U_tx>
        <Username>{target_user}</Username>
        <AllowedSenders>{new_email}</AllowedSenders>
        <CheckPassword>false</CheckPassword>
        <FeedbackType>0</FeedbackType>
        <FeedbackFormat>0</FeedbackFormat>
        <FeedbackWithTIF>false</FeedbackWithTIF>
        <AuthenticateBySignature>false</AuthenticateBySignature>
        <AuthenticateByTickets>false</AuthenticateByTickets>
        <DefaultDeleteAfterUsage>false</DefaultDeleteAfterUsage>
      </U_tx>
    </SetUserTxProperties>
  </soap:Body>
</soap:Envelope>"""

    try:
        # Sending the POST request
        response = requests.post(url, data=xml_payload, headers=headers)
        
        # Check if the HTTP request was successful
        if response.status_code == 200:
            print("Successfully connected to API.")
            print("Response Content:")
            print(response.text)
            
            # Simple check for the Result code (0 usually indicates success in Interfax)
            if "<SetUserTxPropertiesResult>0</SetUserTxPropertiesResult>" in response.text:
                print("\nResult: Success (Code 0)")
            else:
                print("\nResult: The API returned a non-zero code. Check documentation for error details.")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    set_user_allowed_senders()