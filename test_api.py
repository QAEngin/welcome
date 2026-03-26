from flask import Flask, jsonify, send_file, render_template
import os
import re
import io
import requests
from dotenv import load_dotenv

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ======================
# INIT
# ======================
load_dotenv()

app = Flask(__name__, template_folder="templates")

CRM_URL = os.getenv("CRM_URL")
FIREBERRY_TOKENID = os.getenv("FIREBERRY_TOKENID")
CREDENTIALS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
FIREBERRY_ENDPOINT = os.getenv("FIREBERRY_ENDPOINT")

DRIVE_FOLDER_ID = "1MOdZ1gTYGizpKlc6CtErskM_KMRp-2Db"


# ======================
# HELPERS
# ======================

def get_drive_service():
    scope = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    return build("drive", "v3", credentials=creds)


def extract_order_id(filename):
    match = re.search(r'(\d+)\.wav$', filename)
    return match.group(1) if match else ""


def get_domain_from_crm(crmordernumber):
    try:
        headers = {"tokenid": FIREBERRY_ENDPOINT}

        body = {
            "objecttype": 1,
            "page_size": 1,
            "page_number": 1,
            "fields": "pcfsystemfield179,CrmOrder",
            "query": f"(CrmOrder = '{crmordernumber}')"   # ✅ FIX HERE
        }

        #print("CRM request body:", body)  # 👈 DEBUG
        

        r = requests.post(CRM_URL, headers=headers, json=body, timeout=20)
        r.raise_for_status()

        data = r.json()
        print("CRM response:", data)  # 👈 DEBUG

        rows = data.get("data", {}).get("Data", [])

        if not rows:
            return ""

        return (rows[0].get("pcfsystemfield179") or "").strip()

    except Exception as e:
        print("CRM error:", e)
        return ""


# ======================
# ROUTES
# ======================

# 👉 MAIN PAGE → loads record.html
@app.route("/")
def home():
    return render_template("record.html")


# 👉 optional route (same page)
@app.route("/recordings")
def recordings_page():
    return render_template("record.html")


@app.route("/recordings-data")
def recordings_data():

    print("👉 recordings-data called")

    service = get_drive_service()

    results = service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='audio/wav'",
        fields="files(id, name)"
    ).execute()

    print("👉 Drive response:", results)

    files = results.get("files", [])

    output = []

    for f in files:
        name = f["name"]
        file_id = f["id"]

        order_id = extract_order_id(name)
        domain = ""

        if order_id:
            domain = get_domain_from_crm(order_id)

        output.append({
            "name": name,
            "file_id": file_id,
            "order_id": order_id,
            "domain": domain
        })

    print("👉 output:", output)

    return jsonify(output)


@app.route("/download-record/<file_id>/<domain>")
def download_record(file_id, domain):

    service = get_drive_service()

    request_drive = service.files().get_media(fileId=file_id)

    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request_drive)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_data.seek(0)

    if domain == "nodomain":
        domain = ""

    filename = f"{domain}_IVR.wav" if domain else "record_IVR.wav"

    return send_file(
        file_data,
        mimetype="audio/wav",
        as_attachment=True,
        download_name=filename
    )


# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(port=5066, debug=True)