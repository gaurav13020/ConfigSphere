# Auth and RBAC

## Authentication

- Keycloak is the identity provider for V2.
- Services validate bearer tokens in production mode.
- The current slice includes a development fallback controlled by `AUTH_DEV_MODE=true`.

## Authorization

- Authorization is enforced in the control plane.
- Service-scoped RBAC is stored in PostgreSQL.
- Roles:
  - `CONFIG_AUTHOR`
  - `CONFIG_REVIEWER`
  - `CONFIG_IMPLEMENTER`
  - `CONFIG_ADMIN`
  - `CONFIG_AUDITOR`

## Current implementation notes

- On first authenticated request, the user is upserted into the `users` table.
- Roles are seeded automatically.
- Delivery currently accepts the same authentication helper for consistency.
- The first global admin is created explicitly through `POST /v1/admin/bootstrap`.
- Bootstrap is allowed only when no global `CONFIG_ADMIN` binding exists.
- After bootstrap, only global admins can manage user role bindings.

## Admin and bootstrap flow

- `GET /v1/admin/bootstrap/status`
  - returns whether the system still requires the first global admin
- `POST /v1/admin/bootstrap`
  - grants the current authenticated user a global `CONFIG_ADMIN` binding
  - allowed only once, when global admin count is zero
- `GET /v1/admin/users`
  - lists users for admin management
- `GET /v1/admin/users/{user_id}/bindings`
  - lists the user’s current role bindings
- `POST /v1/admin/role-bindings`
  - grants a role to a target user with `GLOBAL` or `SERVICE` scope
- `DELETE /v1/admin/role-bindings/{binding_id}`
  - revokes an existing role binding
- `GET /v1/admin/audit`
  - lists RBAC audit events for grants and revokes

## Audit

- RBAC changes are stored in PostgreSQL in `rbac_audit_events`.
- Governance actions remain stored in:
  - `config_change_actions`
  - `config_change_comments`
  - `config_revision_reviews`
