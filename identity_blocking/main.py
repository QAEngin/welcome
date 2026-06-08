from firebase_functions import https_fn, identity_fn


ALLOWED_DOMAIN = "nimbusip.com"


def _ensure_allowed_domain(event: identity_fn.AuthBlockingEvent) -> None:
    email = (event.data.email or "").strip().lower() if event.data else ""
    if not email.endswith(f"@{ALLOWED_DOMAIN}"):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            message="Unauthorized email domain.",
        )


@identity_fn.before_user_created()
def before_user_created(
    event: identity_fn.AuthBlockingEvent,
) -> identity_fn.BeforeCreateResponse | None:
    _ensure_allowed_domain(event)
    return None


@identity_fn.before_user_signed_in()
def before_user_signed_in(
    event: identity_fn.AuthBlockingEvent,
) -> identity_fn.BeforeSignInResponse | None:
    _ensure_allowed_domain(event)
    return None
