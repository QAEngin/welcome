import json
from datetime import datetime, timezone
from typing import Any

try:
    import firebase_admin
    from firebase_admin import auth, credentials
except ImportError:  # pragma: no cover - handled at runtime
    firebase_admin = None
    auth = None
    credentials = None


ROLE_ADMIN = "admin"
ROLE_USER = "user"


class FirebaseAdminNotConfigured(RuntimeError):
    pass


class FirebaseAdminService:
    def __init__(self, config):
        self.config = config
        self._app = None

    def is_available(self) -> bool:
        return firebase_admin is not None

    def initialize(self):
        if self._app is not None:
            return self._app
        if firebase_admin is None or auth is None:
            raise FirebaseAdminNotConfigured(
                "firebase-admin is not installed. Add it to requirements and deploy again."
            )

        existing = firebase_admin._apps.get("sms-manager-auth")  # type: ignore[attr-defined]
        if existing is not None:
            self._app = existing
            return self._app

        cred = None
        if self.config.firebase_admin_credentials:
            raw = self.config.firebase_admin_credentials
            if raw.startswith("{"):
                cred = credentials.Certificate(json.loads(raw))
            else:
                cred = credentials.Certificate(raw)
        else:
            cred = credentials.ApplicationDefault()

        self._app = firebase_admin.initialize_app(
            cred,
            {"projectId": self.config.identity_platform_project_id or None},
            name="sms-manager-auth",
        )
        return self._app

    def verify_id_token(self, id_token: str) -> dict[str, Any]:
        self.initialize()
        return auth.verify_id_token(id_token, app=self._app, check_revoked=True)

    def get_user(self, uid: str):
        self.initialize()
        return auth.get_user(uid, app=self._app)

    def get_user_by_email(self, email: str):
        self.initialize()
        return auth.get_user_by_email(email, app=self._app)

    def create_user(self, email: str, password: str):
        self.initialize()
        return auth.create_user(email=email, password=password, app=self._app)

    def update_user(self, uid: str, **kwargs):
        self.initialize()
        return auth.update_user(uid, app=self._app, **kwargs)

    def set_role(self, uid: str, role: str):
        self.initialize()
        claims = {
            "role": role,
            "admin": role == ROLE_ADMIN,
        }
        auth.set_custom_user_claims(uid, claims, app=self._app)
        return self.get_user(uid)

    def disable_user(self, uid: str, disabled: bool):
        return self.update_user(uid, disabled=disabled)

    def generate_password_reset_link(self, email: str) -> str:
        self.initialize()
        kwargs = {}
        if self.config.password_reset_redirect_url:
            kwargs["action_code_settings"] = auth.ActionCodeSettings(
                url=self.config.password_reset_redirect_url
            )
        return auth.generate_password_reset_link(email, app=self._app, **kwargs)

    def list_users(
        self,
        email_filter: str = "",
        status_filter: str = "",
        created_from: str = "",
        created_to: str = "",
        page_token: str | None = None,
        max_results: int = 200,
    ) -> tuple[list[dict[str, Any]], str | None]:
        self.initialize()
        exported: list[dict[str, Any]] = []
        next_token = page_token
        scan_guard = 0
        email_filter = email_filter.strip().lower()
        status_filter = status_filter.strip().lower()
        created_from_dt = _parse_date(created_from, end_of_day=False)
        created_to_dt = _parse_date(created_to, end_of_day=True)

        while len(exported) < max_results and scan_guard < 10:
            scan_guard += 1
            page = auth.list_users(page_token=next_token, max_results=1000, app=self._app)
            for user in page.users:
                mapped = self.serialize_user(user)
                if email_filter and email_filter not in mapped["email"].lower():
                    continue
                if status_filter == "enabled" and mapped["disabled"]:
                    continue
                if status_filter == "disabled" and not mapped["disabled"]:
                    continue
                created_at = _parse_iso(mapped["created_at"])
                if created_from_dt and created_at and created_at < created_from_dt:
                    continue
                if created_to_dt and created_at and created_at > created_to_dt:
                    continue
                exported.append(mapped)
                if len(exported) >= max_results:
                    break
            next_token = page.next_page_token
            if not next_token:
                break
        return exported, next_token

    def serialize_user(self, user) -> dict[str, Any]:
        claims = user.custom_claims or {}
        role = resolve_role_from_claims(claims)
        return {
            "uid": user.uid,
            "email": user.email or "",
            "disabled": bool(user.disabled),
            "role": role,
            "created_at": _millis_to_iso(getattr(user.user_metadata, "creation_timestamp", None)),
            "last_sign_in_at": _millis_to_iso(getattr(user.user_metadata, "last_sign_in_timestamp", None)),
        }


def _millis_to_iso(value: Any) -> str:
    if not value:
        return ""
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_date(value: str, end_of_day: bool) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end_of_day:
            return dt.replace(hour=23, minute=59, second=59)
        return dt
    except ValueError:
        return None


def resolve_role_from_claims(claims: dict[str, Any] | None) -> str:
    claims = claims or {}
    role = str(claims.get("role") or "").strip().lower()
    if role == ROLE_ADMIN:
        return ROLE_ADMIN
    if claims.get("admin") is True:
        return ROLE_ADMIN
    return ROLE_USER
