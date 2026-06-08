from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from i18n import DEFAULT_LANGUAGE, normalize_language, translate
from services.identity_platform_service import AuthenticationError


auth_bp = Blueprint("auth", __name__)


def _t(key):
    return translate(normalize_language(session.get("lang", DEFAULT_LANGUAGE)), key)


@auth_bp.route("/login", methods=["GET"])
def login():
    if session.get("uid"):
        return redirect(url_for("home"))
    return render_template("login.html", error="")


@auth_bp.route("/forgot-password", methods=["GET"])
def forgot_password():
    if session.get("uid"):
        return redirect(url_for("home"))
    return render_template("login.html", reset_mode=True, reset_email="", reset_message="", reset_error="")


@auth_bp.route("/forgot-password", methods=["POST"])
def request_password_reset():
    if session.get("uid"):
        return redirect(url_for("home"))

    email = (request.form.get("email") or "").strip().lower()
    if not email:
        return (
            render_template(
                "login.html",
                reset_mode=True,
                reset_email=email,
                reset_message="",
                reset_error=_t("login.email_required"),
            ),
            400,
        )

    services = current_app.config["SERVICES"]
    try:
        services.identity.send_password_reset_email(email, request.remote_addr or "")
    except AuthenticationError as exc:
        return (
            render_template(
                "login.html",
                reset_mode=True,
                reset_email=email,
                reset_message="",
                reset_error=str(exc),
            ),
            503,
        )
    except Exception:
        return (
            render_template(
                "login.html",
                reset_mode=True,
                reset_email=email,
                reset_message="",
                reset_error=_t("login.reset_unavailable"),
            ),
            503,
        )

    return render_template(
        "login.html",
        reset_mode=True,
        reset_email=email,
        reset_message=_t("login.reset_sent"),
        reset_error="",
    )


@auth_bp.route("/auth/login", methods=["POST"])
def perform_login():
    if session.get("uid"):
        return redirect(url_for("home"))

    email = (request.form.get("email") or request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    services = current_app.config["SERVICES"]

    try:
        auth_session = services.identity.sign_in(email, password, request.remote_addr or "")
    except AuthenticationError as exc:
        return render_template("login.html", error=str(exc)), 401
    except Exception:
        return render_template("login.html", error=_t("login.invalid")), 401

    selected_lang = normalize_language(session.get("lang", DEFAULT_LANGUAGE))
    session.clear()
    session.update(auth_session)
    session["lang"] = selected_lang
    session.permanent = True
    return redirect(url_for("home"))


@auth_bp.route("/logout")
def logout():
    services = current_app.config["SERVICES"]
    if session.get("uid"):
        services.audit.write_event(
            action="auth.logout",
            status="ok",
            actor_email=session.get("email", ""),
            actor_uid=session.get("uid", ""),
            target_email=session.get("email", ""),
            target_uid=session.get("uid", ""),
            source="app",
        )
    selected_lang = normalize_language(session.get("lang", DEFAULT_LANGUAGE))
    session.clear()
    session["lang"] = selected_lang
    return redirect(url_for("auth.login"))
