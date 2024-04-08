from flask_login import AnonymousUserMixin

from OpenOversight.app.models.database import Department


class AnonymousUser(AnonymousUserMixin):
    id = None

    def is_admin_or_coordinator(self, department: Department) -> bool:
        return False
