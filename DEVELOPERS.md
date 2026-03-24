# ConfigSphere - Developer's Guide

A comprehensive guide for developers working on ConfigSphere codebase.

## 📁 Project Structure Overview

```
configsphere/
├── README.md                      # Main project README
├── API_GUIDE.md                   # API documentation
├── DEPLOYMENT_GUIDE.md            # Deployment instructions
├── TROUBLESHOOTING.md             # Troubleshooting guide
├── DEVELOPERS.md                  # This file
├── .env.example                   # Environment variables template
├── start.sh / start.cmd           # Quick start scripts
│
├── backend/                       # Django backend
│   ├── docker-compose.yml         # Docker Compose (includes frontend)
│   ├── Dockerfile                 # Backend Docker image
│   ├── requirements.txt           # Python dependencies
│   ├── manage.py                  # Django management script
│   ├── pytest.ini                 # Pytest configuration
│   ├── README.md                  # Backend README
│   │
│   ├── config_sphere/             # Django project settings
│   │   ├── settings/
│   │   │   ├── base.py            # Base configuration
│   │   │   ├── local.py           # Development settings
│   │   │   └── production.py      # Production settings
│   │   ├── urls.py                # Main URL router
│   │   ├── wsgi.py                # WSGI application
│   │   └── asgi.py                # ASGI application
│   │
│   ├── apps/                      # Django applications
│   │   ├── schemas/               # Schema management app
│   │   │   ├── models.py          # Schema model
│   │   │   ├── serializers.py     # DRF serializers
│   │   │   ├── views.py           # API views
│   │   │   ├── urls.py            # App URLs
│   │   │   └── migrations/        # Database migrations
│   │   │
│   │   ├── configs/               # Configuration management app
│   │   │   ├── models.py          # ConfigItem & ConfigVersion models
│   │   │   ├── serializers.py     # DRF serializers
│   │   │   ├── views.py           # API views
│   │   │   ├── urls.py            # App URLs
│   │   │   ├── services/
│   │   │   │   ├── config_item_service.py
│   │   │   │   ├── config_version_service.py
│   │   │   │   ├── hierarchy_resolution_service.py
│   │   │   │   ├── schema_validation_service.py
│   │   │   │   └── activation_service.py
│   │   │   └── migrations/        # Database migrations
│   │   │
│   │   ├── audits/                # Audit logging app
│   │   │   ├── models.py          # AuditEvent model
│   │   │   ├── serializers.py     # DRF serializers
│   │   │   ├── views.py           # API views
│   │   │   ├── urls.py            # App URLs
│   │   │   ├── services.py        # Audit service
│   │   │   └── migrations/        # Database migrations
│   │   │
│   │   └── __init__.py
│   │
│   ├── common/                    # Shared utilities
│   │   ├── constants.py           # Enums and constants
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── utils.py               # Utility functions
│   │
│   └── tests/                     # Test directory
│       ├── audits/
│       ├── configs/
│       └── schemas/
│
└── frontend/                      # React frontend
    ├── Dockerfile                 # Production Docker image
    ├── Dockerfile.dev             # Development Docker image
    ├── package.json               # Node.js dependencies
    ├── tsconfig.json              # TypeScript configuration
    ├── tailwind.config.js         # Tailwind CSS configuration
    ├── vite.config.ts             # Vite configuration
    ├── index.html                 # HTML entry point
    ├── README.md                  # Frontend README
    │
    └── src/
        ├── main.tsx               # Application entry point
        ├── App.tsx                # Main app component with routing
        ├── index.css              # Global styles
        │
        ├── components/            # Reusable components
        │   ├── Layout.tsx          # Main layout wrapper
        │   ├── TopBar.tsx          # Header/navbar
        │   ├── Sidebar.tsx         # Navigation sidebar
        │   └── StatsCard.tsx       # Stats display cards
        │
        ├── pages/                 # Page components
        │   ├── Dashboard.tsx       # Dashboard page
        │   ├── Schemas.tsx         # Schema management
        │   ├── ConfigItems.tsx     # Config items management
        │   ├── ConfigVersions.tsx  # Versions management
        │   ├── ResolvedConfig.tsx  # Config resolver
        │   └── AuditTrail.tsx      # Audit log viewer
        │
        ├── services/              # API integration
        │   └── api.ts             # Axios API client
        │
        ├── stores/                # State management
        │   └── app.ts             # Zustand global store
        │
        ├── types/                 # TypeScript types
        │   └── index.ts           # All type definitions
        │
        └── utils/                 # Utility functions
```

## 🔤 Code Style Guide

### Backend (Python/Django)

#### Naming Conventions
```python
# Models
class ConfigItem:  # PascalCase
    config_key = models.CharField()  # snake_case for fields

# Functions/Methods
def get_resolved_config():  # snake_case
    pass

# Constants
MAX_CONFIG_SIZE = 1000000  # UPPER_SNAKE_CASE

# Private methods
def _internal_helper():  # Prefix with underscore
    pass
```

#### Imports
```python
# Standard library first
import os
from datetime import datetime

# Third-party libraries
from django.db import models
from rest_framework import serializers

# Local imports
from common.exceptions import ConfigSpherException
from .models import ConfigItem
```

#### Type Hints (Python 3.10+)
```python
def get_config(item_id: int) -> Optional[ConfigVersion]:
    """Fetch config version by ID."""
    pass

def create_item(data: dict[str, Any]) -> ConfigItem:
    """Create config item from data."""
    pass
```

### Frontend (TypeScript/React)

#### Naming Conventions
```typescript
// Components
const Dashboard = (): JSX.Element => {
  return <div>Dashboard</div>;
};

// Interfaces/Types
interface ConfigItem {
  id: number;
  key: string;
}

// Functions
const formatDate = (date: Date): string => {
  return date.toLocaleDateString();
};

// Constants
const MAX_ITEMS_PER_PAGE = 50;

// Private/Internal
const _internalHelper = (): void => {
  // Internal logic
};
```

#### Component Structure
```typescript
import { FC, useState } from 'react';
import { Button } from '@mui/material';
import { apiClient } from '@/services/api';
import { useAppStore } from '@/stores/app';
import { ConfigItem } from '@/types';

interface Props {
  id: number;
  onUpdate?: () => void;
}

export const ConfigItemComponent: FC<Props> = ({ id, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const store = useAppStore();

  // Component logic here

  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

## 🛣️ Adding New Features

### Adding a New API Endpoint

#### 1. Create Model (if needed)
```python
# apps/configs/models.py
class ConfigSnapshot(models.Model):
    config_item = models.ForeignKey(ConfigItem, on_delete=models.CASCADE)
    snapshot_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 2. Create Serializer
```python
# apps/configs/serializers.py
class ConfigSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigSnapshot
        fields = ['id', 'config_item', 'snapshot_data', 'created_at']
```

#### 3. Create ViewSet
```python
# apps/configs/views.py
class ConfigSnapshotViewSet(viewsets.ModelViewSet):
    queryset = ConfigSnapshot.objects.all()
    serializer_class = ConfigSnapshotSerializer
    
    def list(self, request, *args, **kwargs):
        """List all snapshots"""
        return super().list(request, *args, **kwargs)
```

#### 4. Register URL
```python
# apps/configs/urls.py
router = DefaultRouter()
router.register(r'snapshots', ConfigSnapshotViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

#### 5. Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding a New Frontend Page

#### 1. Create Page Component
```typescript
// src/pages/NewFeature.tsx
import { FC } from 'react';
import { Layout } from '@/components/Layout';

const NewFeature: FC = () => {
  return (
    <Layout>
      <div>New Feature Page</div>
    </Layout>
  );
};

export default NewFeature;
```

#### 2. Add Route
```typescript
// src/App.tsx
import NewFeature from './pages/NewFeature';

<Routes>
  {/* ... existing routes ... */}
  <Route path="/new-feature" element={<NewFeature />} />
</Routes>
```

#### 3. Add Menu Item
```typescript
// src/components/Sidebar.tsx
const MENU_ITEMS = [
  // ... existing items ...
  { label: 'New Feature', path: '/new-feature', icon: Icon },
];
```

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
docker compose exec web pytest tests/ -v

# Run specific test file
docker compose exec web pytest tests/configs/test_models.py -v

# Run with coverage
docker compose exec web pytest tests/ --cov=apps --cov-report=html

# Run specific test
docker compose exec web pytest tests/configs/test_models.py::TestConfigItem::test_create -v
```

#### Writing Tests
```python
# tests/configs/test_models.py
import pytest
from apps.configs.models import ConfigItem

@pytest.mark.django_db
class TestConfigItem:
    def test_create_config_item(self):
        """Test creating a config item"""
        item = ConfigItem.objects.create(
            key='test_key',
            scope_level='global',
            global_name='default'
        )
        assert item.id is not None
        assert item.key == 'test_key'
```

### Frontend Testing

```bash
# Currently using manual testing through UI
# To add automated tests:

cd frontend
npm install --save-dev vitest @testing-library/react @testing-library/user-event

# Run tests
npm run test
```

## 🚀 Deployment Workflow

### Development
1. Create feature branch: `git checkout -b feature/xyz`
2. Make changes and test locally
3. Commit: `git commit -m "Add feature xyz"`
4. Push: `git push origin feature/xyz`
5. Create Pull Request

### Staging
1. Merge PR to `develop` branch
2. Run full test suite
3. Deploy to staging environment
4. Test in staging environment

### Production
1. Merge `develop` to `main` branch
2. Tag release: `git tag v1.0.0`
3. Deploy docker images
4. Run migrations
5. Monitor logs and metrics

## 🔍 Debugging

### Backend Debugging

```python
# Use Django shell
python manage.py shell

# Check data
from apps.configs.models import ConfigItem
ConfigItem.objects.all()

# Set breakpoint
import pdb; pdb.set_trace()
```

### Frontend Debugging

```javascript
// Browser DevTools
// F12 to open → Console, Network, Application tabs

// React Developer Tools Chrome extension
// Install from Chrome Web Store

// Add console logs
console.log('Debug info:', variable);

// Check API calls
// Network tab → Filter by XHR
```

## 📚 Important Concepts

### Serializers
- Convert model instances to/from JSON
- Validate input data
- Handle nested relationships

### ViewSets
- Combine multiple views into one class
- Automatically handle CRUD operations
- Register with router for URLs

### Middleware
- CORS handling
- Security middleware
- Authentication

### Stores (Zustand)
- Global state management
- Reactive and efficient
- No providers needed

## 🔐 Security Considerations

### Backend
- Validate all inputs
- Use parameterized queries (ORM does this)
- Never log sensitive data
- Use environment variables for secrets
- Implement rate limiting for production

### Frontend
- Sanitize user input
- Use Content Security Policy headers
- Don't store sensitive data in localStorage
- Validate API responses
- Use HTTPS in production

## 🔗 Database Schema Tips

### Indexes
```python
class ConfigItem(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['scope_level', 'global_name']),
            models.UniqueConstraint(
                fields=['key', 'scope_level', 'scope_id'],
                name='unique_config_key_scope'
            ),
        ]
```

### Query Optimization
```python
# Bad - N+1 queries
items = ConfigItem.objects.all()
for item in items:
    print(item.schema.name)  # Query for each item

# Good - Prefetch related
items = ConfigItem.objects.select_related('schema')
for item in items:
    print(item.schema.name)  # No additional queries
```

## 📝 Git Workflow

```bash
# Clone repository
git clone <repo-url>

# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my feature"

# Push to remote
git push origin feature/my-feature

# Create Pull Request on GitHub

# After merge, update local
git checkout main
git pull origin main
```

## 🆘 Common Developer Tasks

### Adding environment variable
```python
# In settings/base.py
MY_VAR = os.environ.get("MY_VAR", "default_value")

# Use in code
from django.conf import settings
value = settings.MY_VAR
```

### Creating async task
```python
# Use Celery in production (not included in starter)
# For now, use signals for async behavior

from django.db.models.signals import post_save

@receiver(post_save, sender=ConfigVersion)
def on_version_created(sender, instance, created, **kwargs):
    if created:
        # Do something async
        pass
```

### Adding logging
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## 📖 Useful Resources

- Django Documentation: https://docs.djangoproject.com
- Django REST Framework: https://www.django-rest-framework.org
- React Documentation: https://react.dev
- TypeScript Documentation: https://www.typescriptlang.org
- PostgreSQL Documentation: https://www.postgresql.org/docs
- Vite Guide: https://vitejs.dev/guide

## 🎯 Code Review Checklist

Before submitting code for review:

- [ ] Tests written and passing
- [ ] No console.log or print statements left
- [ ] No commented-out code
- [ ] Type hints are complete (Python) or TypeScript types are used (Frontend)
- [ ] Docstrings/comments added for complex logic
- [ ] No hardcoded values
- [ ] Environment variables used for configuration
- [ ] Error handling implemented
- [ ] Performance considered
- [ ] Security reviewed
- [ ] Code formatted consistently

---

**Last Updated**: March 2026  
**Version**: 1.0.0

Happy Coding! 🚀
