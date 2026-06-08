import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = (os.environ.get(name) or "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = (os.environ.get(name) or "").strip()
    if not value:
        return default
    return int(value)


@dataclass(frozen=True)
class AppConfig:
    secret_key: str
    token_inforu: str
    sms_url: str
    sms_token: str
    fireberry_tokenid: str
    crm_url: str
    google_application_credentials: str
    drive_folder_id: str
    drive_done_folder_name: str
    identity_platform_project_id: str
    identity_platform_web_api_key: str
    identity_platform_auth_domain: str
    firebase_admin_credentials: str
    allowed_email_domain: str
    session_cookie_secure: bool
    session_lifetime_minutes: int
    app_env: str
    app_commit_sha: str
    audit_log_file: str
    password_reset_redirect_url: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        secret_key = (os.environ.get("SECRET_KEY") or "").strip()
        app_env = (os.environ.get("APP_ENV") or "development").strip()
        if not secret_key:
            if app_env in {"test", "testing"}:
                secret_key = "test-secret-key"
            else:
                raise RuntimeError("SECRET_KEY must be configured.")

        return cls(
            secret_key=secret_key,
            token_inforu=(os.environ.get("TOKEN_INFORU") or "").strip(),
            sms_url=(os.environ.get("SMS_URL") or "").strip(),
            sms_token=(os.environ.get("SMS_TOKEN") or "").strip(),
            fireberry_tokenid=(os.environ.get("FIREBERRY_TOKENID") or "").strip(),
            crm_url=(os.environ.get("CRM_URL") or "").strip(),
            google_application_credentials=(
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "credentials.json"
            ).strip(),
            drive_folder_id=(
                os.environ.get("DRIVE_FOLDER_ID") or "1MOdZ1gTYGizpKlc6CtErskM_KMRp-2Db"
            ).strip(),
            drive_done_folder_name=(os.environ.get("DRIVE_DONE_FOLDER_NAME") or "Done").strip(),
            identity_platform_project_id=(
                os.environ.get("IDENTITY_PLATFORM_PROJECT_ID") or ""
            ).strip(),
            identity_platform_web_api_key=(
                os.environ.get("IDENTITY_PLATFORM_WEB_API_KEY") or ""
            ).strip(),
            identity_platform_auth_domain=(
                os.environ.get("IDENTITY_PLATFORM_AUTH_DOMAIN") or ""
            ).strip(),
            firebase_admin_credentials=(
                os.environ.get("FIREBASE_ADMIN_CREDENTIALS") or ""
            ).strip(),
            allowed_email_domain=(os.environ.get("ALLOWED_EMAIL_DOMAIN") or "nimbusip.com").strip().lower(),
            session_cookie_secure=_env_bool("SESSION_COOKIE_SECURE", app_env != "development"),
            session_lifetime_minutes=_env_int("SESSION_LIFETIME_MINUTES", 60),
            app_env=app_env,
            app_commit_sha=(os.environ.get("APP_COMMIT_SHA") or "").strip(),
            audit_log_file=(os.environ.get("AUDIT_LOG_FILE") or os.path.join("log", "audit.jsonl")).strip(),
            password_reset_redirect_url=(os.environ.get("PASSWORD_RESET_REDIRECT_URL") or "").strip(),
        )
