class ConfigSphereRole:
    VIEWER = "viewer"
    OPERATOR = "operator"
    APPROVER = "approver"
    ADMIN = "admin"

    CHOICES = [
        (VIEWER, "Viewer"),
        (OPERATOR, "Operator"),
        (APPROVER, "Approver"),
        (ADMIN, "Admin"),
    ]

    # Role hierarchy — higher value = more privileged
    HIERARCHY = {
        VIEWER: 0,
        OPERATOR: 1,
        APPROVER: 2,
        ADMIN: 3,
    }

    @classmethod
    def has_minimum_role(cls, user_role: str, min_role: str) -> bool:
        return cls.HIERARCHY.get(user_role, -1) >= cls.HIERARCHY.get(min_role, 999)
