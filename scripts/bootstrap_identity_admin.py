import argparse
import os

from config import AppConfig
from services.firebase_admin_service import FirebaseAdminService, ROLE_ADMIN


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the first Identity Platform admin user.")
    parser.add_argument(
        "--email",
        default=os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@nimbusip.com"),
        help="Admin email to promote.",
    )
    args = parser.parse_args()

    config = AppConfig.from_env()
    service = FirebaseAdminService(config)
    user = service.get_user_by_email(args.email.strip().lower())
    service.set_role(user.uid, ROLE_ADMIN)
    print(f"Promoted {args.email} to admin.")


if __name__ == "__main__":
    main()
