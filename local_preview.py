from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from i18n import DEFAULT_LANGUAGE, direction_for, normalize_language, translate, translations_json


app = Flask(__name__, template_folder="template", static_folder="template", static_url_path="")
app.secret_key = "local-preview"

PREVIEW_USER = "preview@nimbusip.com"
PREVIEW_ROLE = "admin"


@app.context_processor
def inject_preview_user():
    current_lang = normalize_language(session.get("lang", DEFAULT_LANGUAGE))
    return {
        "current_user": PREVIEW_USER,
        "current_role": PREVIEW_ROLE,
        "is_admin": True,
        "lang": current_lang,
        "dir": direction_for(current_lang),
        "i18n_json": translations_json(current_lang),
        "t": lambda key: translate(current_lang, key),
    }


@app.route("/set-language/<language>")
def set_language(language):
    session["lang"] = normalize_language(language)
    return redirect(request.referrer or url_for("home"))


@app.route("/")
def root():
    return redirect(url_for("home"))


@app.route("/login")
def login():
    return render_template("login.html", error="")


@app.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("login.html", reset_mode=True, reset_email="", reset_message="", reset_error="")


@app.route("/forgot-password", methods=["POST"])
def request_password_reset():
    email = (request.form.get("email") or "").strip().lower()
    return render_template(
        "login.html",
        reset_mode=True,
        reset_email=email,
        reset_message="Preview mode: a password reset email would be sent if this account exists.",
        reset_error="",
    )


@app.route("/auth/login", methods=["POST"])
def perform_login():
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/home")
def home():
    return render_template("home.html", active_nav="home")


@app.route("/sms")
def sms_page():
    return render_template("index.html", active_nav="sms")


@app.route("/bot")
def bot_page():
    return render_template("bot.html", active_nav="bot")


@app.route("/record")
def record_page():
    return render_template("record.html", active_nav="record")


@app.route("/admin/users")
def admin_users():
    if request.args.get("format") == "json":
        return admin_users_json()
    return render_template("admin_users.html", active_nav="users")


@app.route("/admin/audit")
def audit_log():
    if request.args.get("format") == "json":
        return admin_audit_json()
    return render_template("audit_log.html", active_nav="audit")


@app.route("/dashboard-data")
def dashboard_data():
    return jsonify(
        {
            "sms": {"waiting": 12, "active_users": ["maya@nimbusip.com", PREVIEW_USER]},
            "bot": {"waiting": 4, "active_users": ["support@nimbusip.com"]},
            "recordings": {"waiting": 7, "active_users": [PREVIEW_USER]},
        }
    )


@app.route("/load-data")
def load_data():
    return jsonify(
        [
            {
                "sheet_row": 312,
                "name": "Nimbus Telecom Demo",
                "text": "שלום, שירות ה-SMS מוכן לבדיקה. נא לאשר Domain ו-DID לפני שליחה.",
                "status": "ממתין",
                "idnumber": "514123456",
                "domain": "demo.nimbusip.com",
                "did": "0735551200",
                "numbercgr": "0501234567",
                "cgr_row": 312,
                "cgr_marked": False,
            },
            {
                "sheet_row": 313,
                "name": "Cloud Voice Ltd",
                "text": "בדיקת הודעה עם טקסט ארוך כדי לוודא שהטבלה נשארת קריאה ולא שוברת את הפריסה.",
                "status": "ממתין",
                "idnumber": "515987321",
                "domain": "",
                "did": "",
                "numbercgr": "",
                "cgr_row": "",
                "cgr_marked": False,
            },
        ]
    )


@app.route("/fireberry-by-id", methods=["POST"])
def fireberry_by_id():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "ok": True,
            "found": True,
            "domain": "customer.nimbusip.com",
            "did": "0735551000",
            "idnumber": payload.get("idnumber", ""),
        }
    )


@app.route("/mark-done", methods=["POST"])
@app.route("/create-sms", methods=["POST"])
@app.route("/send-inforu-mail", methods=["POST"])
@app.route("/bot-done", methods=["POST"])
@app.route("/mark-done/<file_id>", methods=["POST"])
def ok_response(file_id: str | None = None):
    return jsonify({"ok": True, "file_id": file_id, "updated": 1, "results": []})


@app.route("/inforu-log")
def inforu_log():
    return "=== Preview log ===\nNimbus Telecom Demo\tdemo.nimbusip.com\t0735551200\n"


@app.route("/export", methods=["POST"])
def export_csv():
    return "name,domain,did\nNimbus Telecom Demo,demo.nimbusip.com,0735551200\n", {
        "Content-Type": "text/csv"
    }


@app.route("/bot-data")
def bot_data():
    return jsonify(
        {
            "count": 2,
            "customers": [
                {"name": "לקוח לדוגמה", "client_id": "514123456", "domain": "bot.nimbusip.com", "did": "0735551300", "status": "ממתין", "row": 44},
                {"name": "Demo Customer", "client_id": "515987321", "domain": "", "did": "", "status": "ממתין", "row": 45},
            ],
        }
    )


@app.route("/recordings-data")
def recordings_data():
    return jsonify(
        [
            {"name": "call-2026-04-27-1015.wav", "order_id": "ORD-1042", "domain": "voice.nimbusip.com", "file_id": "preview-1"},
            {"name": "call-2026-04-27-1030.wav", "order_id": "ORD-1043", "domain": "", "file_id": "preview-2"},
        ]
    )


@app.route("/download-record/<file_id>/<domain>")
def download_record(file_id: str, domain: str):
    return f"Preview download for {file_id} / {domain}\n"


def admin_users_json():
    now = datetime.now(timezone.utc).isoformat()
    return jsonify(
        {
            "users": [
                {
                    "email": PREVIEW_USER,
                    "disabled": False,
                    "role": "admin",
                    "created_at": now,
                    "last_sign_in_at": now,
                    "uid": "preview-admin",
                },
                {
                    "email": "agent@nimbusip.com",
                    "disabled": False,
                    "role": "user",
                    "created_at": now,
                    "last_sign_in_at": "",
                    "uid": "preview-agent",
                },
            ]
        }
    )


@app.route("/admin/users", methods=["POST"])
@app.route("/admin/users/<uid>/disable", methods=["POST"])
@app.route("/admin/users/<uid>/role", methods=["POST"])
@app.route("/admin/users/<uid>/reset-password", methods=["POST"])
def admin_api_user_action(uid: str | None = None):
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "ok": True,
            "uid": uid,
            "user": {
                "email": payload.get("email", "created@nimbusip.com"),
                "role": payload.get("role", "user"),
            },
            "reset_link": "https://preview.local/reset-password",
        }
    )


def admin_audit_json():
    now = datetime.now(timezone.utc).isoformat()
    return jsonify(
        {
            "events": [
                {
                    "timestamp": now,
                    "actor_email": PREVIEW_USER,
                    "target_email": "agent@nimbusip.com",
                    "action": "admin.user.role_update",
                    "status": "ok",
                    "source": "local-preview",
                    "metadata": {"role": "user"},
                },
                {
                    "timestamp": now,
                    "actor_email": "agent@nimbusip.com",
                    "target_email": "agent@nimbusip.com",
                    "action": "auth.login_succeeded",
                    "status": "ok",
                    "source": "identity-platform",
                    "metadata": {},
                },
            ]
        }
    )


@app.route("/admin/audit/export")
def admin_audit_export():
    return "timestamp,actor,action,status\npreview,preview@nimbusip.com,auth.login_succeeded,ok\n", {
        "Content-Type": "text/csv"
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
