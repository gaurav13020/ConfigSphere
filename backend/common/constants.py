class ScopeLevel:
    GLOBAL = "global"
    REGION = "region"
    GROUP = "group"
    SERVICE = "service"

    CHOICES = [
        (GLOBAL, "Global"),
        (REGION, "Region"),
        (GROUP, "Group"),
        (SERVICE, "Service"),
    ]

    # Precedence: lower number = lower priority (overridden by higher)
    PRECEDENCE = {
        GLOBAL: 0,
        REGION: 1,
        GROUP: 2,
        SERVICE: 3,
    }


class VersionStatus:
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    ARCHIVED = "archived"

    CHOICES = [
        (DRAFT, "Draft"),
        (VALIDATED, "Validated"),
        (ACTIVE, "Active"),
        (ARCHIVED, "Archived"),
    ]


class ConfigItemStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"

    CHOICES = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    ]


class AuditEventType:
    SCHEMA_CREATED = "schema_created"
    CONFIG_ITEM_CREATED = "config_item_created"
    CONFIG_VERSION_CREATED = "config_version_created"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    VERSION_ACTIVATED = "version_activated"
    VERSION_ARCHIVED = "version_archived"
    RESOLVED_CONFIG_FETCHED = "resolved_config_fetched"
    APPROVAL_SUBMITTED = "approval_submitted"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"


class ConfigSphereRole:
    VIEWER = "viewer"
    OPERATOR = "operator"
    APPROVER = "approver"
    ADMIN = "admin"
