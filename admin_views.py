from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session

from authz import admin_required
from services.firebase_admin_service import ROLE_ADMIN, ROLE_USER


admin_bp = Blueprint("admin", __name__)


def _services():
    return current_app.config["SERVICES"]


def _actor():
    return {
        "actor_email": session.get("email", ""),
        "actor_uid": session.get("uid", ""),
    }


@admin_bp.route("/admin/users", methods=["GET"])
@admin_required
def admin_users():
    if request.args.get("format") == "json":
        users, next_page_token = _services().firebase_admin.list_users(
            email_filter=request.args.get("email", ""),
            status_filter=request.args.get("status", ""),
            created_from=request.args.get("created_from", ""),
            created_to=request.args.get("created_to", ""),
            page_token=request.args.get("page_token") or None,
        )
        return jsonify({"users": users, "next_page_token": next_page_token})
    return render_template("admin_users.html", active_nav="users")


@admin_bp.route("/admin/users", methods=["POST"])
@admin_required
def create_admin_user():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or ROLE_USER).strip().lower()
    if role not in {ROLE_ADMIN, ROLE_USER}:
        return jsonify({"ok": False, "message": "Invalid role"}), 400
    if not _services().identity.is_email_allowed(email):
        return jsonify({"ok": False, "message": "Email must belong to the allowed domain"}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "message": "Password must be at least 6 characters"}), 400

    user = _services().firebase_admin.create_user(email=email, password=password)
    _services().firebase_admin.set_role(user.uid, role)
    serialized = _services().firebase_admin.serialize_user(_services().firebase_admin.get_user(user.uid))
    _services().audit.write_event(
        action="admin.user_created",
        status="ok",
        target_email=email,
        target_uid=user.uid,
        metadata={"role": role},
        **_actor(),
    )
    return jsonify({"ok": True, "user": serialized})


@admin_bp.route("/admin/users/<uid>/disable", methods=["POST"])
@admin_required
def disable_admin_user(uid: str):
    payload = request.get_json(silent=True) or {}
    disabled = bool(payload.get("disabled", True))
    updated = _services().firebase_admin.disable_user(uid, disabled)
    serialized = _services().firebase_admin.serialize_user(updated)
    _services().audit.write_event(
        action="admin.user_disabled" if disabled else "admin.user_enabled",
        status="ok",
        target_email=serialized["email"],
        target_uid=uid,
        metadata={"disabled": disabled},
        **_actor(),
    )
    return jsonify({"ok": True, "user": serialized})


@admin_bp.route("/admin/users/<uid>/reset-password", methods=["POST"])
@admin_required
def reset_admin_user_password(uid: str):
    user = _services().firebase_admin.get_user(uid)
    link = _services().firebase_admin.generate_password_reset_link(user.email)
    _services().audit.write_event(
        action="admin.password_reset_link_generated",
        status="ok",
        target_email=user.email,
        target_uid=uid,
        **_actor(),
    )
    return jsonify({"ok": True, "reset_link": link})


@admin_bp.route("/admin/users/<uid>/role", methods=["POST"])
@admin_required
def change_admin_user_role(uid: str):
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip().lower()
    if role not in {ROLE_ADMIN, ROLE_USER}:
        return jsonify({"ok": False, "message": "Invalid role"}), 400
    updated = _services().firebase_admin.set_role(uid, role)
    serialized = _services().firebase_admin.serialize_user(updated)
    _services().audit.write_event(
        action="admin.role_changed",
        status="ok",
        target_email=serialized["email"],
        target_uid=uid,
        metadata={"role": role},
        **_actor(),
    )
    return jsonify({"ok": True, "user": serialized})


@admin_bp.route("/admin/audit", methods=["GET"])
@admin_required
def admin_audit():
    if request.args.get("format") == "json":
        events = _services().audit.list_events(
            actor=request.args.get("actor", ""),
            action=request.args.get("action", ""),
            start_date=request.args.get("start_date", ""),
            end_date=request.args.get("end_date", ""),
        )
        return jsonify({"events": events})
    return render_template("audit_log.html", active_nav="audit")


@admin_bp.route("/admin/audit/export", methods=["GET"])
@admin_required
def admin_audit_export():
    events = _services().audit.list_events(
        actor=request.args.get("actor", ""),
        action=request.args.get("action", ""),
        start_date=request.args.get("start_date", ""),
        end_date=request.args.get("end_date", ""),
        max_results=1000,
    )
    output = _services().audit.export_csv(events)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="audit_log.csv")
