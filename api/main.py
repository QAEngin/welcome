import hashlib
import hmac
import json
import logging
import os
import random
import re
import secrets
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from flask import Flask, jsonify, make_response, request
from google.cloud import firestore


PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "hot-business-welcome-static")
PROJECT_NUMBER = os.environ.get("GCP_PROJECT_NUMBER", "888414270832")
SUPPORT_WHATSAPP_NUMBER = os.environ.get("SUPPORT_WHATSAPP_NUMBER", "972778066666")
OTP_TTL_SECONDS = int(os.environ.get("OTP_TTL_SECONDS", "300"))
OTP_MAX_ATTEMPTS = int(os.environ.get("OTP_MAX_ATTEMPTS", "5"))
OTP_RESEND_SECONDS = int(os.environ.get("OTP_RESEND_SECONDS", "60"))
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", "3600"))
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}
LOCAL_DEV_ORIGIN_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")
CRM_TIMEOUT_SECONDS = float(os.environ.get("CRM_TIMEOUT_SECONDS", "12"))
SMS_TIMEOUT_SECONDS = float(os.environ.get("SMS_TIMEOUT_SECONDS", "12"))

SESSION_SECRET = os.environ.get("SESSION_SECRET")
OTP_PEPPER = os.environ.get("OTP_PEPPER", SESSION_SECRET or "")

DEFAULT_CRM_FIELD_MAP = {
    "customer_id": ["id", "customer_id", "account_id", "accountnumber"],
    "business_id": ["business_id", "ltd_number", "company_id", "hp", "חפ", "ח.פ"],
    "main_phone": ["main_phone", "business_phone", "telephone", "phone", "טלפון ראשי"],
    "mobile": ["mobile", "mobile_phone", "cellular", "cellphone", "טלפון נייד"],
    "active": ["active", "is_active", "status", "account_status"],
    "name": ["name", "account_name", "company_name", "שם לקוח"],
    "services": ["services", "active_services"],
}

DEFAULT_SERVICE_FIELDS = {
    "phones": ["phones", "business_numbers", "numbers"],
    "sms": ["sms", "sms_service"],
    "mail2fax": ["mail2fax", "fax", "mail_to_fax"],
    "recordings": ["recordings", "call_recordings"],
    "yealink": ["yealink", "phones_service"],
}

app = Flask(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
db = firestore.Client(project=PROJECT_ID)


class ApiError(Exception):
    def __init__(self, status_code, code, message, support_reason=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.support_reason = support_reason


def now_ts():
    return int(time.time())


def utc_now():
    return datetime.now(timezone.utc)


def json_error(status_code, code, message, support_reason=None):
    payload = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if support_reason:
        payload["support"] = {
            "reason": support_reason,
            "whatsapp_url": build_whatsapp_url(support_reason),
        }
    return jsonify(payload), status_code


@app.errorhandler(ApiError)
def handle_api_error(error):
    return json_error(
        error.status_code,
        error.code,
        error.message,
        error.support_reason,
    )


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unhandled customer portal API error")
    return json_error(500, "internal_error", "שגיאה זמנית. נסו שוב מאוחר יותר.")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin and (
        origin in ALLOWED_ORIGINS
        or "*" in ALLOWED_ORIGINS
        or LOCAL_DEV_ORIGIN_RE.match(origin)
    ):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/customer/<path:_path>", methods=["OPTIONS"])
def cors_preflight(_path):
    return ("", 204)


@app.route("/api/fireberry-proxy", methods=["OPTIONS"])
def fireberry_proxy_preflight():
    return ("", 204)


def require_json():
    if not request.is_json:
        raise ApiError(400, "invalid_content_type", "יש לשלוח בקשה בפורמט JSON.")
    return request.get_json(silent=True) or {}


def normalize_digits(value):
    return re.sub(r"\D+", "", str(value or ""))


def normalize_phone(value):
    digits = normalize_digits(value)
    if digits.startswith("972"):
        return "0" + digits[3:]
    return digits


def sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sign_value(value):
    if not SESSION_SECRET:
        raise ApiError(500, "missing_session_secret", "הגדרת אבטחה חסרה בשרת.")
    return hmac.new(
        SESSION_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def encode_token(session_id, expires_at):
    body = f"{session_id}.{expires_at}"
    return f"{body}.{sign_value(body)}"


def decode_token(token):
    parts = (token or "").split(".")
    if len(parts) != 3:
        raise ApiError(401, "unauthorized", "נדרשת התחברות מחדש.")
    session_id, expires_at, signature = parts
    body = f"{session_id}.{expires_at}"
    if not hmac.compare_digest(signature, sign_value(body)):
        raise ApiError(401, "unauthorized", "נדרשת התחברות מחדש.")
    if int(expires_at) < now_ts():
        raise ApiError(401, "session_expired", "פג תוקף ההתחברות.")
    return session_id


def get_bearer_token():
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get("customer_portal_session", "")


def get_config_json(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        app.logger.warning("Invalid JSON in %s", name)
        return default


def first_present(source, keys):
    if not isinstance(source, dict):
        return None
    lowered = {str(key).lower(): value for key, value in source.items()}
    for key in keys:
        if key in source:
            return source[key]
        value = lowered.get(str(key).lower())
        if value is not None:
            return value
    return None


def pick_records(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("records", "data", "items", "results", "value"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return [payload]


def is_active_customer(record, field_map):
    value = first_present(record, field_map["active"])
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized in {"active", "פעיל", "1", "true", "yes", "open"}


def map_customer(record):
    field_map = get_config_json("CRM_FIELD_MAP", DEFAULT_CRM_FIELD_MAP)
    service_fields = get_config_json("CRM_SERVICE_FIELD_MAP", DEFAULT_SERVICE_FIELDS)
    services = {}
    for public_name, candidate_keys in service_fields.items():
        services[public_name] = first_present(record, candidate_keys)
    return {
        "customer_id": str(first_present(record, field_map["customer_id"]) or ""),
        "business_id": normalize_digits(first_present(record, field_map["business_id"])),
        "main_phone": normalize_phone(first_present(record, field_map["main_phone"])),
        "mobile": normalize_phone(first_present(record, field_map["mobile"])),
        "name": first_present(record, field_map["name"]) or "",
        "active": is_active_customer(record, field_map),
        "services": services,
        "raw": record,
    }


def crm_headers():
    headers = {"Accept": "application/json"}
    token = os.environ.get("CRM_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    extra = get_config_json("CRM_EXTRA_HEADERS", {})
    headers.update(extra)
    return headers


def crm_url(path_env_name, default_path):
    explicit = os.environ.get(path_env_name)
    if explicit:
        return explicit
    base_url = os.environ.get("CRM_BASE_URL")
    if not base_url:
        raise ApiError(500, "missing_crm_config", "הגדרת CRM חסרה בשרת.")
    return urljoin(base_url.rstrip("/") + "/", default_path.lstrip("/"))


def crm_lookup_customer(business_id, main_phone):
    url = crm_url("CRM_LOOKUP_URL", "/customers/search")
    method = os.environ.get("CRM_LOOKUP_METHOD", "POST").upper()
    payload = {
        "business_id": business_id,
        "main_business_phone": main_phone,
    }
    try:
        if method == "GET":
            response = requests.get(
                url,
                params=payload,
                headers=crm_headers(),
                timeout=CRM_TIMEOUT_SECONDS,
            )
        else:
            response = requests.post(
                url,
                json=payload,
                headers={**crm_headers(), "Content-Type": "application/json"},
                timeout=CRM_TIMEOUT_SECONDS,
            )
        response.raise_for_status()
    except requests.RequestException:
        app.logger.exception("CRM customer lookup failed")
        raise ApiError(502, "crm_unavailable", "לא ניתן לבדוק את פרטי הלקוח כרגע.")

    records = [map_customer(record) for record in pick_records(response.json())]
    exact_matches = [
        record
        for record in records
        if record["business_id"] == business_id
        and record["main_phone"] == main_phone
        and record["active"]
    ]
    if len(exact_matches) != 1:
        raise ApiError(
            404,
            "customer_not_found",
            "לא נמצאה התאמה פעילה לפרטים שהוזנו.",
            "customer_details_missing",
        )
    customer = exact_matches[0]
    if not customer["mobile"]:
        raise ApiError(
            409,
            "mobile_missing",
            "לא מוגדר מספר נייד לאימות במערכת.",
            "mobile_missing",
        )
    if not customer["customer_id"]:
        customer["customer_id"] = sha256(f"{business_id}:{main_phone}")
    return customer


def crm_get_customer(customer_id):
    url = crm_url("CRM_DETAILS_URL", f"/customers/{customer_id}").replace(
        "{customer_id}",
        requests.utils.quote(str(customer_id), safe=""),
    )
    try:
        response = requests.get(
            url,
            headers=crm_headers(),
            timeout=CRM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException:
        app.logger.exception("CRM customer details failed")
        raise ApiError(502, "crm_unavailable", "לא ניתן לטעון את פרטי הלקוח כרגע.")
    return map_customer(response.json())


def send_sms_otp(mobile, code):
    sms_url = os.environ.get("SMS_API_URL")
    sms_token = os.environ.get("SMS_API_TOKEN")
    if not sms_url:
        raise ApiError(500, "missing_sms_config", "הגדרת שליחת SMS חסרה בשרת.")
    message = f"קוד האימות שלך לאזור האישי HOT Business הוא {code}"
    payload = {
        "to": mobile,
        "message": message,
    }
    sender = os.environ.get("SMS_SENDER")
    if sender:
        payload["sender"] = sender
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if sms_token:
        headers["Authorization"] = f"Bearer {sms_token}"
    headers.update(get_config_json("SMS_EXTRA_HEADERS", {}))
    try:
        response = requests.post(
            sms_url,
            json=payload,
            headers=headers,
            timeout=SMS_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException:
        app.logger.exception("SMS OTP send failed")
        raise ApiError(502, "sms_unavailable", "לא ניתן לשלוח קוד אימות כרגע.")


def otp_hash(code, challenge_id):
    secret = OTP_PEPPER or SESSION_SECRET or PROJECT_NUMBER
    return hmac.new(
        secret.encode("utf-8"),
        f"{challenge_id}:{code}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def mask_phone(phone):
    digits = normalize_phone(phone)
    return digits[-4:] if len(digits) >= 4 else "****"


def build_whatsapp_url(reason):
    messages = {
        "mobile_missing": "שלום, ניסיתי להתחבר לאזור האישי אך חסר מספר נייד לאימות בפרטי הלקוח.",
        "customer_details_missing": "שלום, ניסיתי להתחבר לאזור האישי אך פרטי ח.פ או הטלפון הראשי לא נמצאו במערכת.",
        "otp_problem": "שלום, אני צריך עזרה עם קוד האימות לאזור האישי.",
        "service_details_missing": "שלום, אני צריך עזרה עם פרטי השירותים באזור האישי.",
    }
    message = messages.get(reason, "שלום, אני צריך עזרה בהתחברות לאזור האישי.")
    return f"https://wa.me/{SUPPORT_WHATSAPP_NUMBER}?text={requests.utils.quote(message)}"


def check_rate_limit(scope, key, max_requests, window_seconds):
    doc_id = sha256(f"{scope}:{key}")
    doc_ref = db.collection("customer_portal_rate_limits").document(doc_id)
    snapshot = doc_ref.get()
    current = now_ts()
    data = snapshot.to_dict() if snapshot.exists else {}
    window_start = int(data.get("window_start", current))
    count = int(data.get("count", 0))
    if current - window_start >= window_seconds:
        window_start = current
        count = 0
    if count >= max_requests:
        raise ApiError(429, "rate_limited", "בוצעו יותר מדי ניסיונות. נסו שוב מאוחר יותר.")
    doc_ref.set(
        {
            "scope": scope,
            "window_start": window_start,
            "count": count + 1,
            "updated_at": utc_now(),
        },
        merge=True,
    )


@app.route("/api/customer/login/start", methods=["POST"])
def login_start():
    data = require_json()
    business_id = normalize_digits(data.get("business_id"))
    main_phone = normalize_phone(data.get("main_business_phone") or data.get("main_phone"))
    if not business_id or not main_phone:
        raise ApiError(400, "missing_fields", "יש להזין ח.פ ומספר טלפון ראשי.")

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0]
    check_rate_limit("login_ip", ip_address, 20, 3600)
    check_rate_limit("login_business", f"{business_id}:{main_phone}", 5, 900)

    customer = crm_lookup_customer(business_id, main_phone)
    challenge_id = secrets.token_urlsafe(24)
    code = f"{random.SystemRandom().randint(0, 999999):06d}"
    expires_at = now_ts() + OTP_TTL_SECONDS
    db.collection("customer_portal_otp").document(challenge_id).set(
        {
            "customer_id": customer["customer_id"],
            "business_id_hash": sha256(business_id),
            "main_phone_hash": sha256(main_phone),
            "otp_hash": otp_hash(code, challenge_id),
            "masked_mobile": mask_phone(customer["mobile"]),
            "attempts": 0,
            "expires_at": expires_at,
            "created_at": utc_now(),
            "last_sent_at": now_ts(),
            "verified": False,
        }
    )
    send_sms_otp(customer["mobile"], code)
    return jsonify(
        {
            "ok": True,
            "challenge_id": challenge_id,
            "masked_mobile": mask_phone(customer["mobile"]),
            "expires_in": OTP_TTL_SECONDS,
            "resend_after": OTP_RESEND_SECONDS,
        }
    )


@app.route("/api/customer/login/verify", methods=["POST"])
def login_verify():
    data = require_json()
    challenge_id = str(data.get("challenge_id") or "")
    otp_code = normalize_digits(data.get("otp_code"))
    if not challenge_id or not otp_code:
        raise ApiError(400, "missing_fields", "יש להזין את קוד האימות.")

    doc_ref = db.collection("customer_portal_otp").document(challenge_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise ApiError(401, "invalid_otp", "קוד האימות שגוי או שפג תוקפו.", "otp_problem")
    challenge = snapshot.to_dict()
    if challenge.get("verified"):
        raise ApiError(401, "invalid_otp", "קוד האימות כבר נוצל.", "otp_problem")
    if int(challenge.get("expires_at", 0)) < now_ts():
        raise ApiError(401, "otp_expired", "פג תוקף קוד האימות.", "otp_problem")
    attempts = int(challenge.get("attempts", 0))
    if attempts >= OTP_MAX_ATTEMPTS:
        raise ApiError(429, "too_many_attempts", "בוצעו יותר מדי ניסיונות אימות.", "otp_problem")
    if not hmac.compare_digest(challenge.get("otp_hash", ""), otp_hash(otp_code, challenge_id)):
        doc_ref.update({"attempts": attempts + 1, "updated_at": utc_now()})
        raise ApiError(401, "invalid_otp", "קוד האימות שגוי.", "otp_problem")

    session_id = secrets.token_urlsafe(32)
    expires_at = now_ts() + SESSION_TTL_SECONDS
    db.collection("customer_portal_sessions").document(session_id).set(
        {
            "customer_id": challenge["customer_id"],
            "created_at": utc_now(),
            "expires_at": expires_at,
            "revoked": False,
        }
    )
    doc_ref.update({"verified": True, "verified_at": utc_now()})
    token = encode_token(session_id, expires_at)
    response = make_response(
        jsonify(
            {
                "ok": True,
                "expires_in": SESSION_TTL_SECONDS,
            }
        )
    )
    response.set_cookie(
        "customer_portal_session",
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=True,
        samesite="None",
    )
    return response


def require_session():
    token = get_bearer_token()
    session_id = decode_token(token)
    snapshot = db.collection("customer_portal_sessions").document(session_id).get()
    if not snapshot.exists:
        raise ApiError(401, "unauthorized", "נדרשת התחברות מחדש.")
    session = snapshot.to_dict()
    if session.get("revoked") or int(session.get("expires_at", 0)) < now_ts():
        raise ApiError(401, "session_expired", "פג תוקף ההתחברות.")
    return session_id, session


@app.route("/api/customer/me", methods=["GET"])
def customer_me():
    _session_id, session = require_session()
    customer = crm_get_customer(session["customer_id"])
    if not customer["active"]:
        raise ApiError(403, "inactive_customer", "החשבון אינו פעיל.", "customer_details_missing")
    return jsonify(
        {
            "ok": True,
            "customer": {
                "id": customer["customer_id"],
                "name": customer["name"],
                "business_id": customer["business_id"],
                "main_phone": customer["main_phone"],
                "services": customer["services"],
            },
            "support": {
                "whatsapp_url": build_whatsapp_url("service_details_missing"),
            },
        }
    )


@app.route("/api/customer/logout", methods=["POST"])
def logout():
    token = get_bearer_token()
    try:
        session_id = decode_token(token)
        db.collection("customer_portal_sessions").document(session_id).set(
            {"revoked": True, "revoked_at": utc_now()},
            merge=True,
        )
    except ApiError:
        pass
    response = make_response(jsonify({"ok": True}))
    response.delete_cookie("customer_portal_session", samesite="None", secure=True)
    return response


@app.route("/api/fireberry-proxy", methods=["POST"])
def fireberry_proxy():
    """
    Proxy endpoint for Fireberry API calls to avoid CORS issues
    """
    try:
        # Get Fireberry token from environment
        fireberry_token = os.environ.get("FIREBERRY_TOKEN_ID")
        if not fireberry_token:
            raise ApiError(500, "missing_fireberry_config", "הגדרת Fireberry חסרה בשרת.")

        # Get request data
        data = require_json()

        # Forward request to Fireberry API
        fireberry_url = "https://api.fireberry.com/api/v3/query"
        headers = {
            "Content-Type": "application/json",
            "tokenid": fireberry_token
        }

        # Make request to Fireberry
        try:
            response = requests.post(
                fireberry_url,
                json=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            # Return the response as-is
            return jsonify(response.json())

        except requests.RequestException as e:
            app.logger.exception("Fireberry API request failed")
            raise ApiError(502, "fireberry_unavailable", "שירות Fireberry אינו זמין כרגע.")

    except ApiError:
        raise
    except Exception as e:
        app.logger.exception("Fireberry proxy error")
        raise ApiError(500, "proxy_error", "שגיאה בעיבוד הבקשה.")


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify(
        {
            "ok": True,
            "project_id": PROJECT_ID,
            "project_number": PROJECT_NUMBER,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
