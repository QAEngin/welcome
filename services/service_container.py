from services.audit_service import AuditService
from services.firebase_admin_service import FirebaseAdminService
from services.identity_platform_service import IdentityPlatformService


class ServiceContainer:
    def __init__(self, config):
        self.config = config
        self.audit = AuditService(config)
        self.firebase_admin = FirebaseAdminService(config)
        self.identity = IdentityPlatformService(config, self.firebase_admin, self.audit)
