# ConfigSphere — Config Server API

A centralized configuration management system for microservices.
Supports hierarchical config resolution, schema validation, versioning, activation lifecycle, and a full audit trail.

---

## Problem Statement

Managing configuration across large microservice systems is brittle:
- Changes require service restarts
- No governance, approvals, or traceability
- Different teams and regions need isolated overrides
- No rollback when a bad config goes live

ConfigSphere solves this by providing a centralized control plane where configuration is versioned, validated, and resolved hierarchically — and microservices can refresh config without restarting.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Config Server API                  │
│                                                     │
│   Schema Registry → Config Items → Config Versions │
│                  → Activation → Hierarchy Resolver  │
│                  → Audit Trail                      │
└─────────────────────────────────────────────────────┘
              │
              ▼
     Microservice polls
     GET /resolved-config/
     and refreshes in memory
```

### Hierarchy Precedence

```
service  >  group  >  region  >  global
```

Higher scope always wins. A service-level config key overrides the same key at region or global level.

### Layer Structure

```
apps/
├── audits/        # Append-only audit event log
├── schemas/       # JSON Schema definitions
└── configs/       # ConfigItem, ConfigVersion, and all services
    └── services/
        ├── activation_service.py
        ├── config_item_service.py
        ├── config_version_service.py
        ├── hierarchy_resolution_service.py
        └── schema_validation_service.py

common/
├── constants.py   # ScopeLevel, VersionStatus, AuditEventType
├── exceptions.py  # Domain exceptions + custom DRF error handler
└── utils.py       # Checksum, merge helpers
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Database | PostgreSQL 15 |
| Validation | jsonschema (JSON Schema Draft-7) |
| Containerization | Docker + Docker Compose |
| Testing | pytest + pytest-django |

---

## Getting Started

### Prerequisites
- Docker Desktop installed and running

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/<your-username>/configsphere.git
cd configsphere/backend

# Build and start all services (Django + PostgreSQL)
docker compose up --build
```

The API will be available at `http://localhost:8000/api/v1/`

PostgreSQL runs inside Docker — no local installation needed.

### Run Tests

```bash
docker compose exec web python -m pytest tests/ -v
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1/`

### Schema Registry
| Method | Endpoint | Description |
|---|---|---|
| POST | `/schemas/` | Create a JSON Schema definition |
| GET | `/schemas/` | List all schemas |
| GET | `/schemas/{id}/` | Get schema by ID |

### Config Items
| Method | Endpoint | Description |
|---|---|---|
| POST | `/config-items/` | Create a config item at a scope level |
| GET | `/config-items/` | List config items (filterable) |
| GET | `/config-items/{id}/` | Get config item by ID |

### Config Versions
| Method | Endpoint | Description |
|---|---|---|
| POST | `/config-items/{id}/versions/` | Create a new version |
| GET | `/config-items/{id}/versions/` | List all versions for an item |
| GET | `/config-versions/{id}/` | Get version by ID |

### Activation
| Method | Endpoint | Description |
|---|---|---|
| POST | `/config-versions/{id}/activate/` | Activate a validated version |

### Resolved Config
| Method | Endpoint | Description |
|---|---|---|
| GET | `/resolved-config/` | Get merged effective config for a scope |

**Query params:** `?service=payment-service&region=us-west&group=payment-team`

Response includes:
- `payload` — merged effective configuration
- `checksum` — SHA-256 of merged payload
- `layers` — provenance: which scope contributed what
- `ETag` header — for future `If-None-Match` polling support

### Audit Trail
| Method | Endpoint | Description |
|---|---|---|
| GET | `/audit-events/` | List all audit events (filterable) |

**Filter params:** `?event_type=version_activated&config_item_id=1`

---

## Version Lifecycle

```
CREATE version
      │
      ▼
  DRAFT  ──── schema validation fails
      │
  VALIDATED ── schema validation passes (or no schema attached)
      │
  ACTIVE ───── activated via POST /activate/
      │
  ARCHIVED ─── automatically when a newer version is activated
```

- `DRAFT` versions cannot be activated
- Only one `ACTIVE` version per config item at any time
- Activation is atomic — previous active version is archived in the same transaction

---

## Audit Events

Every state change is automatically recorded:

| Event | Trigger |
|---|---|
| `schema_created` | New schema definition saved |
| `config_item_created` | New config item created |
| `config_version_created` | New version created |
| `validation_passed` | Payload passed schema validation |
| `validation_failed` | Payload failed schema validation |
| `version_activated` | Version promoted to active |
| `version_archived` | Previous active version superseded |
| `resolved_config_fetched` | Microservice fetched effective config |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config_sphere.settings.local` | Settings module |
| `DJANGO_SECRET_KEY` | dev key | Django secret key |
| `DB_NAME` | `configsphere` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_HOST` | `db` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |

---

## Roadmap

- [ ] Rollback support
- [ ] Approval workflow
- [ ] RBAC / per-team permissions
- [ ] ETag `If-None-Match` polling in SDK
- [ ] Git-sync for config as code
- [ ] Redis caching layer for resolved config
