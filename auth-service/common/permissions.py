from rest_framework.permissions import BasePermission
from common.constants import ConfigSphereRole


def _has_minimum_role(user, min_role: str) -> bool:
    role = getattr(user, "role", None)
    return ConfigSphereRole.has_minimum_role(role, min_role)


class IsViewer(BasePermission):
    """Grants access to any authenticated user (Viewer and above)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    _has_minimum_role(request.user, ConfigSphereRole.VIEWER))


class IsOperator(BasePermission):
    """Grants access to Operator, Approver, and Admin roles."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    _has_minimum_role(request.user, ConfigSphereRole.OPERATOR))


class IsApprover(BasePermission):
    """Grants access to Approver and Admin roles."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    _has_minimum_role(request.user, ConfigSphereRole.APPROVER))


class IsAdmin(BasePermission):
    """Grants access to Admin role only."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    _has_minimum_role(request.user, ConfigSphereRole.ADMIN))
