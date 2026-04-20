from flask import Flask, jsonify, send_file, render_template
import os
import re
import io
import json
import requests
from dotenv import load_dotenv

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
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
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "1MOdZ1gTYGizpKlc6CtErskM_KMRp-2Db")
DRIVE_DONE_FOLDER_NAME = os.getenv("DRIVE_DONE_FOLDER_NAME", "Done")

if not FIREBERRY_URL:
    raise RuntimeError("CRM_URL not found in .env")


# ======================
# HELPERS
# ======================

def get_drive_service(readonly=True):
    scope = ["https://www.googleapis.com/auth/drive.readonly"] if readonly else ["https://www.googleapis.com/auth/drive"]
    creds_info, creds_source = load_service_account_info()
    try:
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        # Force auth early so we return a clear error to the user.
        creds.refresh(Request())
    except RefreshError as e:
        message = str(e)
        if "invalid_grant" in message or "Invalid JWT Signature" in message:
            raise RuntimeError(
                "Google auth failed: invalid_grant / Invalid JWT Signature. "
                "Use a valid active service-account JSON key for this service account. "
                f"Loaded from: {creds_source}"
            ) from e
        raise RuntimeError(f"Google auth refresh failed ({creds_source}): {message}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Google Drive credentials ({creds_source}): {e}") from e

    return build("drive", "v3", credentials=creds)


def extract_order_id(filename: str) -> str:
    base_name = os.path.splitext(os.path.basename(filename or ""))[0]
    if not base_name:
        return ""

    # Take the first 5 digits from the left side, allowing optional leading spaces.
    start_match = re.match(r"\s*(\d{5})", base_name)
    return start_match.group(1) if start_match else ""


def load_service_account_info():
    creds_source = CREDENTIALS_FILE.strip()
    if not creds_source:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is empty.")

    if creds_source.startswith("{"):
        info = json.loads(creds_source)
        source_label = "GOOGLE_APPLICATION_CREDENTIALS (inline JSON)"
    else:
        abs_path = os.path.abspath(creds_source)
        if not os.path.exists(abs_path):
            raise RuntimeError(f"Credentials file not found: {abs_path}")
        with open(abs_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        source_label = abs_path

    if info.get("type") != "service_account":
        raise RuntimeError(
            f"Credentials must be a service account JSON. "
            f"Found type={info.get('type')!r} in {source_label}"
        )

    private_key = info.get("private_key")
    if not private_key:
        raise RuntimeError(f"Missing private_key in {source_label}")

    # Normalize cases where the key was stored with literal '\\n' sequences.
    if "\\n" in private_key and "\n" not in private_key:
        info["private_key"] = private_key.replace("\\n", "\n")

    return info, source_label


def get_domain_from_crm(crm_order_number: str) -> str:
    if not crm_order_number:
        return ""

    try:
        if not FIREBERRY_TOKENID:
            return ""

        headers = {"tokenid": FIREBERRY_TOKENID}
        # Step 1: find accountid from order object (objecttype 13).
        order_body = {
            "objecttype": 13,
            "page_size": 1,
            "page_number": 1,
            "fields": "accountid,CrmOrderNumber",
            "query": f"(CrmOrderNumber = '{crm_order_number}')",
            "sort_type": "desc"
        }
        order_resp = requests.post(FIREBERRY_URL, headers=headers, json=order_body, timeout=20)
        order_resp.raise_for_status()
        order_rows = order_resp.json().get("data", {}).get("Data", [])
        if not order_rows or not isinstance(order_rows[0], dict):
            return ""

        accountid = str(order_rows[0].get("accountid") or "").strip()
        if not accountid:
            return ""

        # Step 2: query account object (objecttype 1) and return domain.
        account_body = {
            "objecttype": 1,
            "page_size": 1,
            "page_number": 1,
            "fields": "accountid,pcfsystemfield179,accountname",
            "query": f"(accountid = '{accountid}')"
        }
        account_resp = requests.post(FIREBERRY_URL, headers=headers, json=account_body, timeout=20)
        account_resp.raise_for_status()
        account_rows = account_resp.json().get("data", {}).get("Data", [])
        if not account_rows or not isinstance(account_rows[0], dict):
            return ""

        value = account_rows[0].get("pcfsystemfield179")
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
