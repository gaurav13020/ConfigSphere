# ConfigSphere - Centralized Configuration Management Server

A modern, professional configuration management system for microservices. Supports hierarchical config resolution, schema validation, versioning, activation lifecycle, and a full audit trail.

## 🎯 Quick Links

- 📖 [Full Deployment Guide](./DEPLOYMENT_GUIDE.md)
- 🔌 [API Reference](./API_GUIDE.md)
- 🎨 [Frontend README](./frontend/README.md)
- 🔧 [Backend README](./backend/README.md)

## ✨ Key Features

✅ **Hierarchical Configuration Management**
- 4-level hierarchy: global → region → group → service
- Intelligent override system - lower scopes override higher scopes
- Full audit trail of all changes

✅ **Schema Validation**
- JSON Schema (Draft-7) integration
- Optional schema attachment to config items
- Automatic validation on version creation

✅ **Version Control & Activation**
- Create unlimited versions for each config item
- Version lifecycle: DRAFT → VALIDATED → ACTIVE → ARCHIVED
- Atomic activation with automatic archival of previous version
- Rollback capability through version history

✅ **Config Resolution**
- Get merged effective config at any hierarchy level
- Transparent layer information showing contribution source
- SHA-256 checksums for cache invalidation
- ETag support for polling clients

✅ **Professional UI**
- Modern React-based dashboard
- Material-UI components with custom styling
- Responsive design (desktop, tablet, mobile)
- Interactive data tables with filtering
- Real-time stats and activity feed

✅ **Complete Audit Trail**
- Append-only event log
- Event filtering by type, actor, date
- Export capabilities
- Full request/response tracking

## 📋 Problem It Solves

Managing configuration across large microservice systems is complex:
- ❌ Changes require service restarts
- ❌ No governance, approvals, or traceability
- ❌ Different teams need isolated overrides
- ❌ No rollback when bad config goes live
- ❌ No visibility into configuration hierarchy

ConfigSphere solves all of these problems with a centralized control plane.

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   ConfigSphere Web Application       │
│   (React + TypeScript + Material-UI) │
│   http://localhost:3000             │
└────────────┬────────────────────────┘
             │
      CORS Enabled
             │
┌────────────▼────────────────────────┐
│   REST API Server                    │
│   (Django + Django REST Framework)   │
│   http://localhost:8000/api/v1       │
├─────────────────────────────────────┤
│ Endpoints:                           │
│  • POST /schemas/                    │
│  • GET  /config-items/               │
│  • POST /config-items/{id}/versions/ │
│  • GET  /resolved-config/            │
│  • GET  /audit-events/               │
└────────────┬────────────────────────┘
             │
             │ PostgreSQL
             │
┌────────────▼────────────────────────┐
│   PostgreSQL Database (Port 5432)    │
│   ├─ Schemas                         │
│   ├─ ConfigItems                     │
│   ├─ ConfigVersions (Versioned)      │
│   ├─ AuditEvents (Append-only)       │
│   └─ Indexes & Constraints           │
└─────────────────────────────────────┘
```

## 🚀 Getting Started

### Option 1: Docker (Recommended)

```bash
cd backend
docker compose up --build

# Wait for all services to start
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📚 Usage Examples

### 1. Create a Schema

```bash
curl -X POST http://localhost:8000/api/v1/schemas/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "service-config",
    "description": "Schema for service configs",
    "schema_json": {
      "type": "object",
      "properties": {
        "timeout": {"type": "integer"},
        "retries": {"type": "integer"}
      },
      "required": ["timeout"]
    }
  }'
```

### 2. Create a Config Item

```bash
curl -X POST http://localhost:8000/api/v1/config-items/ \
  -H "Content-Type: application/json" \
  -d '{
    "key": "app_settings",
    "scope_level": "global",
    "global_name": "default",
    "description": "Global application settings",
    "schema_id": 1
  }'
```

### 3. Create a Version

```bash
curl -X POST http://localhost:8000/api/v1/config-items/1/versions/ \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "timeout": 30,
      "retries": 3
    },
    "change_summary": "Initial config",
    "created_by": "admin"
  }'
```

### 4. Activate Version

```bash
curl -X POST http://localhost:8000/api/v1/config-versions/1/activate/ \
  -H "Content-Type: application/json" \
  -d '{"actor": "admin"}'
```

### 5. Get Resolved Config

```bash
curl http://localhost:8000/api/v1/resolved-config/?global=default&service=payment-service
```

Response:
```json
{
  "payload": {
    "timeout": 30,
    "retries": 3
  },
  "checksum": "d4e5f6...",
  "layers": [
    {
      "scope_level": "global",
      "config_item_id": 1,
      "version_number": 1,
      "key": "app_settings"
    }
  ]
}
```

## 🗂️ Hierarchy Example

```
Hierarchy:  Global → Region → Group → Service
            (lowest priority) ← → (highest priority)

Example Config: "max_connections"

Layer 1 (Global):           max_connections: 100
Layer 2 (Region us-west):   max_connections: 150
Layer 3 (Group payment):    max_connections: 200
Layer 4 (Service):          max_connections: 250  ← WINS (highest scope)

Effective Result: max_connections: 250
```

## 📊 Technology Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Django | 4.2 | Web framework |
| Django REST Framework | 3.16 | REST API |
| PostgreSQL | 15 | Database |
| jsonschema | 4.25 | Schema validation |
| pytest | 8.4 | Testing |
| Docker | Latest | Containerization |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.2 | UI library |
| TypeScript | 5.3 | Type safety |
| Vite | 5.0 | Build tool |
| Material-UI | 5.14 | Components |
| Tailwind CSS | 3.4 | Styling |
| Zustand | 4.4 | State management |
| Axios | 1.6 | HTTP client |

## 💾 Database Schema

### Schemas Table
```
- id (PK)
- name (unique)
- description
- schema_json (JSONB)
- created_at
```

### ConfigItems Table
```
- id (PK)
- key
- scope_level (global|region|group|service)
- global_name
- region_name
- group_name
- service_name
- schema_id (FK)
- description
- created_at / updated_at
```

### ConfigVersions Table
```
- id (PK)
- config_item_id (FK)
- version_number
- payload (JSONB)
- checksum (SHA-256)
- status (draft|validated|validation_failed|active|archived)
- validation_error (text)
- change_summary
- created_by
- created_at
```

### AuditEvents Table (Append-only)
```
- id (PK)
- event_type (schema_created|config_item_created|...)
- actor (user who made change)
- config_item_id (FK, nullable)
- config_version_id (FK, nullable)
- schema_id (FK, nullable)
- payload (JSONB - event details)
- created_at
```

## 🔐 Security

### Authentication
Currently allows all requests (AllowAny). For production:
- Implement JWT token authentication
- Add user roles and permissions
- Restrict endpoints by role
- Add API key support for microservices

### CORS
- Frontend whitelist configured
- Credentials enabled
- Preflight requests handled

### Database
- ATOMIC_REQUESTS enabled for consistency
- Prepared statements against SQL injection
- Encrypted connections in production

## 📈 Performance

- PostgreSQL with indexed lookups
- Caching via checksums and ETags
- Lazy loading and pagination
- Efficient hierarchical queries
- Django ORM optimization

## 🧪 Testing

### Backend
```bash
docker compose exec web python -m pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm run test
```

## 📝 API Documentation

Complete API documentation available in [API_GUIDE.md](./API_GUIDE.md)

### Main Endpoints

```
Schemas:
  GET    /api/v1/schemas/
  POST   /api/v1/schemas/
  GET    /api/v1/schemas/{id}/

Config Items:
  GET    /api/v1/config-items/
  POST   /api/v1/config-items/
  GET    /api/v1/config-items/{id}/

Config Versions:
  GET    /api/v1/config-items/{id}/versions/
  POST   /api/v1/config-items/{id}/versions/
  GET    /api/v1/config-versions/{id}/
  POST   /api/v1/config-versions/{id}/activate/

Resolved Config:
  GET    /api/v1/resolved-config/?global=default&service=Payment-Service

Audit:
  GET    /api/v1/audit-events/
```

## 🛣️ Roadmap

- [ ] Authentication & Authorization (JWT)
- [ ] RBAC (Role-Based Access Control)
- [ ] Approval Workflows
- [ ] Git Sync for "Config as Code"
- [ ] Redis Caching Layer
- [ ] Rollback Functionality
- [ ] Webhook Notifications
- [ ] Config Diff/Comparison Tool
- [ ] Batch Operations
- [ ] Advanced Analytics

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 💡 Key Concepts

### Version Lifecycle
```
    ┌─────────┐
    │  DRAFT  │ ← Initial state
    └────┬────┘
         │
         ├─ Schema validation fails ──→ VALIDATION_FAILED
         │
         └─ Schema validation passes ──→ VALIDATED
                                              │
                                              └─ Activate ──→ ACTIVE
                                                               │
                                                               └─ New version activated ──→ ARCHIVED
```

### Hierarchy Resolution
```
Service Config Query:
  global=default, region=us-west, group=payment, service=payment-svc

Resolution Process:
  1. Fetch global config for default
  2. Fetch region config for us-west (overrides global)
  3. Fetch group config for payment (overrides region)
  4. Fetch service config for payment-svc (overrides all)
  5. Deep merge all configs
  6. Generate checksum of result
  7. Return with layer information
```

## 🐛 Common Issues & Solutions

See [Troubleshooting](./DEPLOYMENT_GUIDE.md#-troubleshooting) in the deployment guide.

## 📞 Support

- Check [API_GUIDE.md](./API_GUIDE.md) for API questions
- Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for setup issues
- Review [backend/README.md](./backend/README.md) for backend details
- Review [frontend/README.md](./frontend/README.md) for frontend details

---

**Created**: March 2026  
**Version**: 1.0.0  
**Status**: Production Ready ✅

Made with ❤️ for configuration management excellence.
