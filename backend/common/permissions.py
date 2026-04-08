from rest_framework.permissions import BasePermission


class _RoleHierarchy:
    VIEWER = "viewer"
    OPERATOR = "operator"
    APPROVER = "approver"
    ADMIN = "admin"

    _ORDER = {VIEWER: 0, OPERATOR: 1, APPROVER: 2, ADMIN: 3}

    @classmethod
    def has_minimum(cls, user_role: str, min_role: str) -> bool:
        return cls._ORDER.get(user_role, -1) >= cls._ORDER.get(min_role, 999)


def _check(request, min_role: str) -> bool:
    user = request.user
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and _RoleHierarchy.has_minimum(getattr(user, "role", ""), min_role)
    )


class IsViewer(BasePermission):
    """Any authenticated user (Viewer and above)."""
    message = "Authentication required."

    def has_permission(self, request, view):
        return _check(request, _RoleHierarchy.VIEWER)


class IsOperator(BasePermission):
    """Operator, Approver, or Admin."""
    message = "Operator role or above is required."

    def has_permission(self, request, view):
        return _check(request, _RoleHierarchy.OPERATOR)


class IsApprover(BasePermission):
    """Approver or Admin."""
    message = "Approver role or above is required."

    def has_permission(self, request, view):
        return _check(request, _RoleHierarchy.APPROVER)


class IsAdmin(BasePermission):
    """Admin only."""
    message = "Admin role is required."

    def has_permission(self, request, view):
        return _check(request, _RoleHierarchy.ADMIN)
