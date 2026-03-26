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

app = Flask(
    __name__,
    template_folder="template",
    static_folder="template",
    static_url_path=""
)

CRM_URL = (os.getenv("CRM_URL") or "").strip()
FIREBERRY_URL = CRM_URL
FIREBERRY_TOKENID = (os.getenv("FIREBERRY_TOKENID") or "").strip()
CREDENTIALS_FILE = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json") or "").strip()
FIREBERRY_ENDPOINT = (os.getenv("FIREBERRY_ENDPOINT") or "").strip()
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "1MOdZ1gTYGizpKlc6CtErskM_KMRp-2Db")
DRIVE_DONE_FOLDER_NAME = os.getenv("DRIVE_DONE_FOLDER_NAME", "Done")

if not FIREBERRY_URL:
    raise RuntimeError("CRM_URL not found in .env")


# ======================
# HELPERS
# ======================

def get_drive_service(readonly=True):
    scope = ["https://www.googleapis.com/auth/drive.readonly"] if readonly else ["https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    return build("drive", "v3", credentials=creds)


def extract_order_id(filename: str) -> str:
    base_name = os.path.splitext(os.path.basename(filename or ""))[0]
    if not base_name:
        return ""

    # Take the first 5 digits from the left side, allowing optional leading spaces.
    start_match = re.match(r"\s*(\d{5})", base_name)
    return start_match.group(1) if start_match else ""


def get_domain_from_crm(crm_order_number: str) -> str:
    if not crm_order_number:
        return ""

    try:
        # Prefer the dedicated token variable; keep endpoint as backward-compatible fallback.
        token_for_recording = FIREBERRY_TOKENID or FIREBERRY_ENDPOINT
        if not token_for_recording:
            return ""

        headers = {"tokenid": token_for_recording}
        body = {
            "objecttype": 1,
            "page_size": 1,
            "page_number": 1,
            "fields": "Body,pcfsystemfield179,CrmOrder",
            "query": f"(CrmOrder = '{crm_order_number}')"
        }

        r = requests.post(FIREBERRY_URL, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        rows = r.json().get("data", {}).get("Data", [])

        if not rows:
            return ""

        row = rows[0] if isinstance(rows[0], dict) else {}
        value = row.get("Body")
        if value is None:
            value = row.get("pcfsystemfield179")

        return str(value).strip() if value is not None else ""

    except Exception:
        return ""


# ======================
# ROUTES
# ======================

@app.route("/")
def home():
    return render_template("record.html")


@app.route("/recordings")
def recordings_page():
    return render_template("record.html")


@app.route("/recordings-data")
def recordings_data():
    service = get_drive_service(readonly=True)

    results = service.files().list(
        q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='audio/wav' and trashed=false",
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])
    output = []

    for f in files:
        name = f.get("name", "")
        file_id = f.get("id", "")

        order_id = extract_order_id(name)
        domain = get_domain_from_crm(order_id) if order_id else ""

        output.append({
            "name": name,
            "file_id": file_id,
            "order_id": order_id,
            "domain": domain
        })

    return jsonify(output)


@app.route("/download-record/<file_id>/<domain>")
def download_record(file_id, domain):
    service = get_drive_service(readonly=True)

    request_drive = service.files().get_media(fileId=file_id)

    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request_drive)

    done = False
    while not done:
        _, done = downloader.next_chunk()

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


@app.route("/mark-done/<file_id>", methods=["POST"])
def mark_record_done(file_id):
    service = get_drive_service(readonly=False)

    file_meta = service.files().get(fileId=file_id, fields="id,parents").execute()
    current_parents = file_meta.get("parents", [])

    done_query = (
        f"'{DRIVE_FOLDER_ID}' in parents and "
        f"name = '{DRIVE_DONE_FOLDER_NAME}' and "
        "mimeType = 'application/vnd.google-apps.folder' and trashed=false"
    )
    done_search = service.files().list(q=done_query, fields="files(id,name)").execute().get("files", [])

    if done_search:
        done_folder_id = done_search[0]["id"]
    else:
        done_folder = service.files().create(
            body={
                "name": DRIVE_DONE_FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [DRIVE_FOLDER_ID]
            },
            fields="id"
        ).execute()
        done_folder_id = done_folder["id"]

    remove_parents = ",".join(current_parents) if current_parents else ""
    service.files().update(
        fileId=file_id,
        addParents=done_folder_id,
        removeParents=remove_parents,
        fields="id,parents"
    ).execute()

    return jsonify({"ok": True})


# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(port=5066, debug=True)
