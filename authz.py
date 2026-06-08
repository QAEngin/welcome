from functools import wraps

from flask import current_app, g, redirect, session, url_for

from services.firebase_admin_service import ROLE_ADMIN


def get_session_user() -> dict:
    return {
        "uid": session.get("uid", ""),
        "email": session.get("email", ""),
        "role": session.get("role", ""),
        "authenticated_at": session.get("authenticated_at", ""),
        "expires_at": session.get("expires_at", ""),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        services = current_app.config["SERVICES"]
        user = get_session_user()
        if not user["uid"] or not services.identity.is_session_valid(user):
            session.clear()
            return redirect(url_for("auth.login"))
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_session_user()
        if user.get("role") != ROLE_ADMIN:
            return redirect(url_for("home"))
        return view(*args, **kwargs)

    return wrapped
