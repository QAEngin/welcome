import importlib
import io
import json
import os
import unittest

from services.firebase_admin_service import resolve_role_from_claims


class FakeIdentityService:
    def __init__(self):
        self.allowed_domain = "nimbusip.com"
        self.valid = True
        self.reset_requests = []

    def sign_in(self, email, password, remote_addr=""):
        if not email.endswith(f"@{self.allowed_domain}"):
            raise RuntimeError("Invalid email or password")
        if password != "secret123":
            raise RuntimeError("Invalid email or password")
        role = "admin" if email == "admin@nimbusip.com" else "user"
        return {
            "uid": f"uid-{email}",
            "email": email,
            "role": role,
            "authenticated_at": "2026-01-01T00:00:00+00:00",
            "expires_at": "2999-01-01T00:00:00+00:00",
        }

    def is_session_valid(self, session_data):
        return self.valid and bool(session_data.get("uid"))

    def is_email_allowed(self, email):
        return email.endswith(f"@{self.allowed_domain}")

    def send_password_reset_email(self, email, remote_addr=""):
        self.reset_requests.append((email, remote_addr))
        return self.is_email_allowed(email)


class FakeUser:
    def __init__(self, uid, email, disabled=False, role="user"):
        self.uid = uid
        self.email = email
        self.disabled = disabled
        self.role = role
        self.custom_claims = {
            "role": role,
            "admin": role == "admin",
        }


class FakeFirebaseAdminService:
    def __init__(self):
        self.users = {
            "uid-admin@nimbusip.com": FakeUser("uid-admin@nimbusip.com", "admin@nimbusip.com", role="admin"),
            "uid-user@nimbusip.com": FakeUser("uid-user@nimbusip.com", "user@nimbusip.com", role="user"),
        }

    def list_users(self, **kwargs):
        return ([self.serialize_user(user) for user in self.users.values()], None)

    def create_user(self, email, password):
        user = FakeUser(f"uid-{email}", email)
        self.users[user.uid] = user
        return user

    def set_role(self, uid, role):
        self.users[uid].role = role
        self.users[uid].custom_claims = {
            "role": role,
            "admin": role == "admin",
        }
        return self.users[uid]

    def disable_user(self, uid, disabled):
        self.users[uid].disabled = disabled
        return self.users[uid]

    def generate_password_reset_link(self, email):
        return f"https://reset.example/{email}"

    def get_user(self, uid):
        return self.users[uid]

    def get_user_by_email(self, email):
        for user in self.users.values():
            if user.email == email:
                return user
        raise KeyError(email)

    def serialize_user(self, user):
        return {
            "uid": user.uid,
            "email": user.email,
            "disabled": user.disabled,
            "role": user.role,
            "created_at": "2026-01-01T00:00:00+00:00",
            "last_sign_in_at": "",
        }


class FakeAuditService:
    def __init__(self):
        self.events = []

    def write_event(self, **kwargs):
        event = {
            "timestamp": "2026-01-01T00:00:00+00:00",
            "actor_email": kwargs.get("actor_email", ""),
            "actor_uid": kwargs.get("actor_uid", ""),
            "target_email": kwargs.get("target_email", ""),
            "target_uid": kwargs.get("target_uid", ""),
            "action": kwargs.get("action", ""),
            "status": kwargs.get("status", ""),
            "source": kwargs.get("source", "app"),
            "metadata": kwargs.get("metadata", {}),
        }
        self.events.append(event)
        return event

    def list_events(self, **kwargs):
        return list(self.events)

    def export_csv(self, events):
        output = io.BytesIO()
        output.write(b"timestamp,action\n")
        for event in events:
            output.write(f"{event['timestamp']},{event['action']}\n".encode("utf-8"))
        output.seek(0)
        return output


class FakeServices:
    def __init__(self):
        self.identity = FakeIdentityService()
        self.firebase_admin = FakeFirebaseAdminService()
        self.audit = FakeAuditService()


class AuthAdminTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SECRET_KEY"] = "test-secret-key"
        os.environ["APP_ENV"] = "testing"
        os.environ["FIREBERRY_TOKENID"] = "token"
        os.environ["CRM_URL"] = "https://crm.example"
        os.environ["SMS_URL"] = "https://sms.example"
        os.environ["SMS_TOKEN"] = "sms-token"
        os.environ["IDENTITY_PLATFORM_WEB_API_KEY"] = "web-api-key"
        os.environ["IDENTITY_PLATFORM_PROJECT_ID"] = "project-id"
        import app as app_module

        cls.app_module = importlib.reload(app_module)

    def setUp(self):
        self.fake_services = FakeServices()
        self.app = self.app_module.app
        self.app.config["TESTING"] = True
        self.app.config["SERVICES"] = self.fake_services
        self.client = self.app.test_client()

    def login(self, email="admin@nimbusip.com", password="secret123"):
        return self.client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )

    def test_login_success_with_allowed_domain(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/home", response.location)

    def test_login_rejects_other_domain(self):
        response = self.login(email="user@gmail.com")
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid email or password", response.data)

    def test_logout_clears_session(self):
        self.login()
        response = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_forgot_password_sends_reset_request(self):
        response = self.client.post(
            "/forgot-password",
            data={"email": "user@nimbusip.com"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"password reset email has been sent", response.data)
        self.assertEqual(self.fake_services.identity.reset_requests[0][0], "user@nimbusip.com")

    def test_forgot_password_requires_email(self):
        response = self.client.post("/forgot-password", data={"email": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Enter your Nimbus email address", response.data)

    def test_admin_access_denied_for_user(self):
        self.login(email="user@nimbusip.com")
        response = self.client.get("/admin/users", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/home", response.location)

    def test_admin_access_allowed_for_admin(self):
        self.login()
        response = self.client.get("/admin/users?format=json")
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data)
        self.assertIn("users", payload)

    def test_create_disable_and_change_role(self):
        self.login()
        create_response = self.client.post(
            "/admin/users",
            json={"email": "new@nimbusip.com", "password": "secret123", "role": "user"},
        )
        self.assertEqual(create_response.status_code, 200)
        created_user = create_response.get_json()["user"]

        disable_response = self.client.post(
            f"/admin/users/{created_user['uid']}/disable",
            json={"disabled": True},
        )
        self.assertEqual(disable_response.status_code, 200)
        self.assertTrue(disable_response.get_json()["user"]["disabled"])

        role_response = self.client.post(
            f"/admin/users/{created_user['uid']}/role",
            json={"role": "admin"},
        )
        self.assertEqual(role_response.status_code, 200)
        self.assertEqual(role_response.get_json()["user"]["role"], "admin")

    def test_reset_password_generates_audit_event(self):
        self.login()
        response = self.client.post("/admin/users/uid-user@nimbusip.com/reset-password")
        self.assertEqual(response.status_code, 200)
        self.assertIn("reset_link", response.get_json())
        actions = [event["action"] for event in self.fake_services.audit.events]
        self.assertIn("admin.password_reset_link_generated", actions)

    def test_audit_export_returns_csv(self):
        self.login()
        self.fake_services.audit.write_event(action="auth.login_succeeded", status="ok")
        response = self.client.get("/admin/audit/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)


class ClaimResolutionTestCase(unittest.TestCase):
    def test_admin_boolean_claim_maps_to_admin(self):
        self.assertEqual(resolve_role_from_claims({"admin": True}), "admin")

    def test_role_claim_maps_to_admin(self):
        self.assertEqual(resolve_role_from_claims({"role": "admin"}), "admin")

    def test_missing_claims_default_to_user(self):
        self.assertEqual(resolve_role_from_claims({}), "user")


if __name__ == "__main__":
    unittest.main()
