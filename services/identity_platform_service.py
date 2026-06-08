from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from services.firebase_admin_service import (
    FirebaseAdminNotConfigured,
    ROLE_USER,
    resolve_role_from_claims,
)


class AuthenticationError(RuntimeError):
    pass


class IdentityPlatformService:
    def __init__(self, config, firebase_admin_service, audit_service):
        self.config = config
        self.firebase_admin_service = firebase_admin_service
        self.audit_service = audit_service

    def is_email_allowed(self, email: str) -> bool:
        domain = self.config.allowed_email_domain.lower().lstrip("@")
        return email.strip().lower().endswith(f"@{domain}")

    def send_password_reset_email(self, email: str, remote_addr: str = "") -> bool:
        normalized_email = email.strip().lower()
        if not normalized_email:
            raise AuthenticationError("Email is required")

        if not self.is_email_allowed(normalized_email):
            self.audit_service.write_event(
                action="auth.password_reset_requested",
                status="blocked",
                actor_email=normalized_email,
                target_email=normalized_email,
                source="identity-platform",
                metadata={"ip_address": remote_addr, "reason": "domain_not_allowed"},
            )
            return False

        api_key = self.config.identity_platform_web_api_key
        if not api_key:
            raise AuthenticationError("Password reset is not configured")

        payload = {
            "requestType": "PASSWORD_RESET",
            "email": normalized_email,
        }
        if self.config.password_reset_redirect_url:
            payload["continueUrl"] = self.config.password_reset_redirect_url

        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
            json=payload,
            timeout=20,
        )

        self.audit_service.write_event(
            action="auth.password_reset_requested",
            status="ok" if response.status_code == 200 else "error",
            actor_email=normalized_email,
            target_email=normalized_email,
            source="identity-platform",
            metadata={"http_status": response.status_code, "ip_address": remote_addr},
        )
        return response.status_code == 200

    def sign_in(self, email: str, password: str, remote_addr: str = "") -> dict[str, Any]:
        normalized_email = email.strip().lower()
        if not normalized_email or not password:
            raise AuthenticationError("Invalid email or password")

        if not self.is_email_allowed(normalized_email):
            self.audit_service.write_event(
                action="auth.domain_blocked",
                status="blocked",
                actor_email=normalized_email,
                target_email=normalized_email,
                source="identity-platform",
                metadata={"ip_address": remote_addr},
            )
            raise AuthenticationError("Invalid email or password")

        api_key = self.config.identity_platform_web_api_key
        if not api_key:
            raise AuthenticationError("Identity Platform is not configured")

        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={
                "email": normalized_email,
                "password": password,
                "returnSecureToken": True,
            },
            timeout=20,
        )

        if response.status_code != 200:
            self.audit_service.write_event(
                action="auth.login_failed",
                status="error",
                actor_email=normalized_email,
                target_email=normalized_email,
                source="identity-platform",
                metadata={"http_status": response.status_code},
            )
            raise AuthenticationError("Invalid email or password")

        payload = response.json()
        id_token = payload.get("idToken", "")
        if not id_token:
            raise AuthenticationError("Invalid email or password")

        try:
            decoded = self.firebase_admin_service.verify_id_token(id_token)
        except FirebaseAdminNotConfigured as exc:
            raise AuthenticationError(str(exc)) from exc
        except Exception as exc:
            raise AuthenticationError("Failed to verify identity token") from exc

        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(seconds=int(payload.get("expiresIn", "3600")))
        role, role_debug = self._resolve_role(decoded, normalized_email)

        session_data = {
            "uid": decoded.get("uid") or decoded.get("sub") or payload.get("localId"),
            "email": normalized_email,
            "role": role,
            "authenticated_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        self.audit_service.write_event(
            action="auth.login_succeeded",
            status="ok",
            actor_email=normalized_email,
            actor_uid=session_data["uid"],
            target_email=normalized_email,
            target_uid=session_data["uid"],
            source="identity-platform",
            metadata={"role": role, "ip_address": remote_addr, "role_debug": role_debug},
        )
        return session_data

    def is_session_valid(self, session_data: dict[str, Any]) -> bool:
        expires_at = session_data.get("expires_at")
        if not expires_at:
            return False
        try:
            return datetime.now(timezone.utc) < datetime.fromisoformat(expires_at)
        except ValueError:
            return False

    def _resolve_role(self, decoded_token: dict[str, Any], email: str) -> tuple[str, dict[str, Any]]:
        debug: dict[str, Any] = {
            "token_uid": decoded_token.get("uid") or decoded_token.get("sub") or "",
            "token_claims": _extract_claim_snapshot(decoded_token),
            "resolution_source": "default_user",
            "fetched_uid_claims": None,
            "fetched_email_claims": None,
        }
        token_role = resolve_role_from_claims(decoded_token)
        if token_role != ROLE_USER:
            debug["resolution_source"] = "token"
            return token_role, debug

        uid = decoded_token.get("uid") or decoded_token.get("sub")
        if uid:
            try:
                user = self.firebase_admin_service.get_user(uid)
                uid_claims = user.custom_claims or {}
                debug["fetched_uid_claims"] = _extract_claim_snapshot(uid_claims)
                uid_role = resolve_role_from_claims(uid_claims)
                if uid_role != ROLE_USER:
                    debug["resolution_source"] = "uid_lookup"
                    return uid_role, debug
            except Exception:
                pass

        if email:
            try:
                user = self.firebase_admin_service.get_user_by_email(email)
                email_claims = user.custom_claims or {}
                debug["fetched_email_claims"] = _extract_claim_snapshot(email_claims)
                email_role = resolve_role_from_claims(email_claims)
                if email_role != ROLE_USER:
                    debug["resolution_source"] = "email_lookup"
                    return email_role, debug
            except Exception:
                pass

        return ROLE_USER, debug


def _extract_claim_snapshot(claims: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": claims.get("role"),
        "admin": claims.get("admin"),
        "keys": sorted(list(claims.keys())),
    }
