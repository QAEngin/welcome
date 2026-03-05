from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import io
import pandas as pd
import gspread
import requests
from datetime import datetime
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from flask import session, redirect, url_for

load_dotenv()

app = Flask(
    __name__,
    template_folder="template",
    static_folder="template",
    static_url_path=""
)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")
APP_USERNAME = os.environ.get("APP_USERNAME")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# ====== CONFIG ======
SPREADSHEET_ID = "1uwtREvtWENPabibI5FSlhdYokIbBs_kuZmYVeL-BgCQ"
SHEET_NAME = "SMS"

# NumberCGR pool sheet
CGR_SHEET_NAME = "חיפ_סמס"
CGR_START_ROW = 312
CGR_COL_NUMBER = 1  # A
CGR_COL_MARK = 3    # B (checkbox/mark)

# Column mapping (1-based for gspread)
COL_NAME = 1       # A
COL_IDNUMBER = 2   # B (ח.פ) hidden in UI
COL_STATUS = 8     # H
COL_SMS_TEXT = 10  # J
COL_K = 11         # K

STATUS_PENDING = "ממתין"
STATUS_DONE = "בוצע"
K_REQUIRED_VALUE = "לקוח הותקן"

# ENV
CREDENTIALS_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
FIREBERRY_TOKENID = os.environ.get("FIREBERRY_TOKENID")
FIREBERRY_URL = os.environ.get("CRM_URL")

if not FIREBERRY_TOKENID:
    raise RuntimeError("FIREBERRY_TOKENID not found in .env")
if not FIREBERRY_URL:
    raise RuntimeError("CRM_URL not found in .env")

# Logging
LOG_DIR = "log"
LOG_FILE = os.path.join(LOG_DIR, "created.log")


def ensure_log_file():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("")


def append_log(customers):
    """
    customers: list of dicts with keys: name, domain, did
    """
    ensure_log_file()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"=== {ts} | Status -> {STATUS_DONE} | Count: {len(customers)} ===\n")
        f.write("שם לקוח\tDomain\tDID\n")
        for c in customers:
            name = (c.get("name") or "").strip()
            domain = (c.get("domain") or "").strip()
            did = (c.get("did") or "").strip()
            f.write(f"{name}\t{domain}\t{did}\n")
        f.write("\n")


def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    return gspread.authorize(creds)


def digits_only(s: str) -> str:
    return re.sub(r"\D+", "", (s or "").strip())


def first_number_clean(value: str) -> str:
    """
    Take the first number chunk from a string, keep only digits.
    If length >= 10 -> return first 10
    If length == 9 -> return 9
    Else -> return whatever digits exist
    """
    raw = (value or "").strip()
    if not raw:
        return ""

    parts = re.split(r"[\s,;]+", raw)
    for p in parts:
        d = digits_only(p)
        if d:
            if len(d) >= 10:
                return d[:10]
            if len(d) == 9:
                return d
            return d

    d = digits_only(raw)
    if not d:
        return ""
    if len(d) >= 10:
        return d[:10]
    if len(d) == 9:
        return d
    return d


def fireberry_lookup_by_idnumber(idnumber: str) -> dict:
    id_digits = digits_only(idnumber)
    if not id_digits:
        return {"found": False, "domain": "", "did": ""}

    headers = {"tokenid": FIREBERRY_TOKENID}
    body = {
        "objecttype": 1,
        "page_size": 50,
        "page_number": 1,
        "fields": "pcfsystemfield179,accountname,pcfsystemfield256,pcfsystemfield164,pcfsystemfield166",
        "query": f"(idnumber = {id_digits})",
        "sort_type": "desc"
    }

    r = requests.post(FIREBERRY_URL, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    resp = r.json()

    rows = []
    if isinstance(resp, dict):
        inner = resp.get("data")
        if isinstance(inner, dict) and isinstance(inner.get("Data"), list):
            rows = inner.get("Data", [])

    if not rows or not isinstance(rows[0], dict):
        return {"found": False, "domain": "", "did": ""}

    row = rows[0]
    domain = (row.get("pcfsystemfield179") or "").strip()

    main_raw = (row.get("pcfsystemfield166") or "").strip()
    range_raw = (row.get("pcfsystemfield164") or "").strip()
    did_raw = main_raw if main_raw else range_raw
    did = first_number_clean(did_raw)

    return {"found": True, "domain": domain, "did": did}


def get_pending_customers():
    """
    Returns customers where:
      H == ממתין AND K == לקוח הותקן
    Also includes:
      - idnumber (hidden)
      - numbercgr from sheet חיפ_סמס!A312.. (aligned by order)
      - cgr_row (for updates on export)
      - cgr_marked (green/yellow indicator from column B)
    """
    client = get_gspread_client()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    data = ws.get_all_values()
    if not data or len(data) < 2:
        return []

    rows = data[1:]
    pending = []

    for i, row in enumerate(rows, start=2):
        status = row[COL_STATUS - 1].strip() if len(row) >= COL_STATUS else ""
        k_value = row[COL_K - 1].strip() if len(row) >= COL_K else ""

        if status != STATUS_PENDING or k_value != K_REQUIRED_VALUE:
            continue

        name = row[COL_NAME - 1].strip() if len(row) >= COL_NAME else ""
        idnumber = row[COL_IDNUMBER - 1].strip() if len(row) >= COL_IDNUMBER else ""
        sms_text = row[COL_SMS_TEXT - 1].strip() if len(row) >= COL_SMS_TEXT else ""

        pending.append({
            "sheet_row": i,
            "name": name,
            "idnumber": idnumber,
            "text": sms_text,
            "status": status
        })

    # Attach NumberCGR from חיפ_סמס
    try:
        if pending:
            cgr_ws = client.open_by_key(SPREADSHEET_ID).worksheet(CGR_SHEET_NAME)
            start = CGR_START_ROW
            end = CGR_START_ROW + len(pending) - 1
            cgr_vals = cgr_ws.get(f"A{start}:B{end}")

            while len(cgr_vals) < len(pending):
                cgr_vals.append([])

            for idx, cust in enumerate(pending):
                row_idx = CGR_START_ROW + idx
                row_vals = cgr_vals[idx] if idx < len(cgr_vals) else []

                a_val = row_vals[0] if len(row_vals) >= 1 else ""
                b_val = row_vals[1] if len(row_vals) >= 2 else ""

                num_digits = digits_only(a_val)
                numbercgr = ""
                if num_digits:
                    numbercgr = num_digits if num_digits.startswith("0") else ("0" + num_digits)

                b_norm = (b_val or "").strip().upper()
                marked = bool(b_norm) and b_norm not in ("FALSE", "0", "NO")

                cust["numbercgr"] = numbercgr
                cust["cgr_row"] = row_idx
                cust["cgr_marked"] = marked

    except Exception:
        for cust in pending:
            cust["numbercgr"] = ""
            cust["cgr_row"] = None
            cust["cgr_marked"] = False

    return pending


@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")
## Login
@app.route("/login", methods=["GET","POST"])
def login():

    # If already logged in → go to main page
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == APP_USERNAME and password == APP_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))

        # Wrong credentials
        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")
## Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/load-data")
def load_data():
    return jsonify(get_pending_customers())


@app.route("/fireberry-by-id", methods=["POST"])
def fireberry_by_id():
    payload = request.get_json(silent=True) or {}
    idnumber = (payload.get("idnumber") or "").strip()

    if not idnumber:
        return jsonify({"ok": False, "message": "Missing idnumber"}), 400

    try:
        result = fireberry_lookup_by_idnumber(idnumber)
        return jsonify({"ok": True, **result})
    except requests.HTTPError as e:
        return jsonify({"ok": False, "message": f"Fireberry HTTP error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"ok": False, "message": f"Error: {str(e)}"}), 500


@app.route("/mark-done", methods=["POST"])
def mark_done():
    payload = request.get_json(silent=True) or {}
    customers = payload.get("customers", [])

    if not isinstance(customers, list) or not customers:
        return jsonify({"ok": False, "message": "No customers provided."}), 400

    rows = []
    clean_customers = []

    for c in customers:
        if not isinstance(c, dict):
            continue
        r = c.get("sheet_row")
        if not isinstance(r, int) or r < 2:
            continue

        name = (c.get("name") or "").strip()
        domain = (c.get("domain") or "").strip()
        did = (c.get("did") or "").strip()

        rows.append(r)
        clean_customers.append({"name": name, "domain": domain, "did": did})

    if not rows:
        return jsonify({"ok": False, "message": "No valid rows to update."}), 400

    client = get_gspread_client()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

    updates = []
    for r in rows:
        updates.append({
            "range": gspread.utils.rowcol_to_a1(r, COL_STATUS),
            "values": [[STATUS_DONE]]
        })

    ws.batch_update(updates)
    append_log(clean_customers)

    return jsonify({"ok": True, "updated": len(rows)})


@app.route("/export", methods=["POST"])
def export_csv():
    data = request.get_json(silent=True)
    if not isinstance(data, list) or not data:
        return jsonify({"ok": False, "message": "No data to export."}), 400

    # Export template:
    # name=Domain, caller_id_number=DID, did=NumberCGR, template=SMS text
    rows_out = []
    updates = []

    for r in data:
        if not isinstance(r, dict):
            continue

        domain = (r.get("Domain") or "").strip()
        caller_id = (r.get("DID") or "").strip()
        numbercgr = (r.get("NumberCGR") or "").strip()
        template_txt = (r.get("Text") or "").strip()
        cgr_row = r.get("cgr_row")

        num_digits = digits_only(numbercgr)
        if num_digits:
            numbercgr = num_digits if num_digits.startswith("0") else ("0" + num_digits)

        rows_out.append({
            "name": domain,
            "caller_id_number": caller_id,
            "did": numbercgr,
            "template": template_txt
        })

        # Update חיפ_סמס Column B with Domain (as requested)
        if isinstance(cgr_row, int) and cgr_row >= 1 and domain:
            updates.append({
                "range": gspread.utils.rowcol_to_a1(cgr_row, CGR_COL_MARK),
                "values": [[domain]]
            })

    # Update Google Sheet חיפ_סמס
    try:
        if updates:
            client = get_gspread_client()
            cgr_ws = client.open_by_key(SPREADSHEET_ID).worksheet(CGR_SHEET_NAME)
            cgr_ws.batch_update(updates)
    except Exception:
        pass

    df = pd.DataFrame(rows_out, columns=["name", "caller_id_number", "did", "template"])

    output = io.BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)

    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="sms_export.csv")


if __name__ == "__main__":
    app.run(port=5059, debug=True)