# ConfigSphere API Guide

> **Base URL:** `http://localhost:8000/api/v1`
> **Content-Type:** `application/json` for all requests

---

## Overview

ConfigSphere is a hierarchical configuration server. Configs are scoped in a 4-level hierarchy:

```
global → region → group → service
```

A config key at a lower scope overrides the same key at a higher scope. Use the **Resolved Config** endpoint to get the final merged config for any scope without doing the merging yourself.

---

## Typical Workflow

```
1. (Optional) Create a Schema       POST /schemas/
2. Create a Config Item             POST /config-items/
3. Create a Version with payload    POST /config-items/{id}/versions/
4. Activate the version             POST /config-versions/{id}/activate/
5. Fetch resolved config            GET  /resolved-config/?service=X&region=Y
```

---

## Scope Levels

| `scope_level` | Required fields |
|---------------|----------------|
| `global`      | `global_name` (default: `"default"`) |
| `region`      | `global_name`, `region_name` |
| `group`       | `global_name`, `region_name`, `group_name` |
| `service`     | `service_name` |

---

## Schemas (Optional)

Schemas validate config payloads against a JSON Schema (Draft-7). You can create config items without a schema — validation is skipped.

### Create a Schema
```
POST /schemas/
```
```json
{
  "name": "service-defaults",
  "description": "Schema for service-level configs",
  "schema_json": {
    "type": "object",
    "properties": {
      "timeout": { "type": "integer" },
      "retries": { "type": "integer" }
    },
    "required": ["timeout"]
  }
}
```

**Response `201`:**
```json
{
  "id": 1,
  "name": "service-defaults",
  "description": "Schema for service-level configs",
  "schema_json": { ... },
  "created_at": "2026-03-22T10:00:00Z"
}
```

### List Schemas
```
GET /schemas/
```

### Get a Schema
```
GET /schemas/{id}/
```

---

## Config Items

A Config Item represents a logical config key at a specific scope. It holds no values itself — values live in versions.

### Create a Config Item
```
POST /config-items/
```
```json
{
  "key": "app_config",
  "scope_level": "global",
  "global_name": "default",
  "description": "Global defaults for all services",
  "schema_id": 1
}
```

> `schema_id` is optional. Omit it to skip payload validation.

**Region-scoped example:**
```json
{
  "key": "app_config",
  "scope_level": "region",
  "global_name": "default",
  "region_name": "us-west",
  "description": "US West overrides"
}
```

**Service-scoped example:**
```json
{
  "key": "app_config",
  "scope_level": "service",
  "service_name": "payment-service",
  "description": "Payment service config"
}
```

**Response `201`:**
```json
{
  "id": 1,
  "key": "app_config",
  "scope_level": "global",
  "global_name": "default",
  "region_name": "",
  "group_name": "",
  "service_name": "",
  "schema": 1,
  "status": "active",
  "active_version_id": null,
  "description": "Global defaults for all services",
  "created_by": null,
  "created_at": "2026-03-22T10:00:00Z",
  "updated_at": "2026-03-22T10:00:00Z"
}
```

### List Config Items
```
GET /config-items/
```

**Filter by query params:**
```
GET /config-items/?scope_level=region
GET /config-items/?scope_level=service&service_name=payment-service
GET /config-items/?key=app_config
```

### Get a Config Item
```
GET /config-items/{id}/
```

---

## Config Versions

A version holds the actual config payload. Create as many versions as needed — only the **activated** version is used in resolution.

### Create a Version
```
POST /config-items/{id}/versions/
```
```json
{
  "payload": {
    "timeout": 30,
    "retries": 3,
    "feature_flags": { "dark_mode": true }
  },
  "change_summary": "initial config",
  "created_by": "alice"
}
```

**Response `201`:**
```json
{
  "id": 5,
  "config_item": 1,
  "version_number": 1,
  "payload": { "timeout": 30, "retries": 3, "feature_flags": { "dark_mode": true } },
  "checksum": "a3f2c1...",
  "status": "draft",
  "validation_error": "",
  "change_summary": "initial config",
  "created_by": "alice",
  "created_at": "2026-03-22T10:01:00Z"
}
```

> Status starts as `draft`. If a schema is attached, it transitions to `validated` or `validation_failed`.

### Activate a Version

Only an activated version is included in resolved config.

```
POST /config-versions/{id}/activate/
```
```json
{
  "actor": "alice"
}
```

**Response `200`:** Returns the version with `status: "active"`.

### List Versions for an Item
```
GET /config-items/{id}/versions/
```

### Get a Version
```
GET /config-versions/{id}/
```

---

## Resolved Config

The most important read endpoint. Returns the **merged effective config** for a given scope by walking up the hierarchy (service → group → region → global) and merging payloads.

```
GET /resolved-config/
```

**Query params:**

| Param    | Description |
|----------|-------------|
| `global` | Global name (default: `"default"`) |
| `region` | Region name |
| `group`  | Group name |
| `service`| Service name |

**Examples:**

Get global config only:
```
GET /resolved-config/?global=default
```

Get config for a region:
```
GET /resolved-config/?global=default&region=us-west
```

Get fully resolved config for a service:
```
GET /resolved-config/?global=default&region=us-west&group=checkout&service=payment-service
```

**Response `200`:**
```json
{
  "payload": {
    "timeout": 30,
    "retries": 5,
    "feature_flags": { "dark_mode": true }
  },
  "checksum": "d4e5f6...",
  "layers": [
    {
      "scope_level": "global",
      "config_item_id": 1,
      "config_version_id": 2,
      "version_number": 1,
      "checksum": "a3f2c1...",
      "key": "app_config"
    },
    {
      "scope_level": "region",
      "config_item_id": 3,
      "config_version_id": 7,
      "version_number": 2,
      "checksum": "b9c3d2...",
      "key": "app_config"
    }
  ],
  "scope_params": {
    "global": "default",
    "region": "us-west",
    "group": null,
    "service": "payment-service"
  }
}
```

> The `checksum` on the response can be used as an **ETag** for cache invalidation. The server also sets the `ETag` response header automatically.

---

## Audit Events

Read-only log of all changes.

### List Audit Events
```
GET /audit-events/
```

**Filter by query params:**
```
GET /audit-events/?event_type=config_item_created
GET /audit-events/?config_item_id=1
GET /audit-events/?ordering=created_at
GET /audit-events/?ordering=-created_at
```

**Event types:**
- `schema_created`
- `config_item_created`
- `config_version_created`
- `validation_passed`
- `validation_failed`
- `version_activated`
- `version_archived`
- `resolved_config_fetched`

---

## Error Responses

All errors follow this structure:

```json
{
  "error": "error_code",
  "message": "Human readable message"
}
```

| HTTP Status | `error` code | When |
|-------------|-------------|------|
| `400` | `validation_error` | Invalid request body |
| `404` | `not_found` | Resource doesn't exist |
| `409` | `conflict` | Duplicate key at same scope |
| `409` | `activation_failed` | Version can't be activated |
| `422` | `validation_failed` | Payload failed schema validation |

**Validation error (400) includes field details:**
```json
{
  "error": "validation_error",
  "message": "...",
  "details": {
    "region_name": ["This field is required for scope_level=region."]
  }
}
```

---

## Quick Reference

```
# Schemas
GET    /api/v1/schemas/
POST   /api/v1/schemas/
GET    /api/v1/schemas/{id}/

# Config Items
GET    /api/v1/config-items/
POST   /api/v1/config-items/
GET    /api/v1/config-items/{id}/

# Config Versions
GET    /api/v1/config-items/{id}/versions/
POST   /api/v1/config-items/{id}/versions/
GET    /api/v1/config-versions/{id}/
POST   /api/v1/config-versions/{id}/activate/

# Resolved Config
GET    /api/v1/resolved-config/?service=X&region=Y&group=Z&global=default

# Audit
GET    /api/v1/audit-events/
```
