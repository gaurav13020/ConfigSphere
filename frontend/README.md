# ConfigSphere Frontend

A modern, professional React-based frontend for ConfigSphere - a centralized configuration management system for microservices.

## 🎨 Features

- **Dashboard**: Real-time overview of schemas, config items, and audit events
- **Schema Management**: Create and manage JSON Schema definitions
- **Config Items**: Organize configurations across 4-level hierarchy (global → region → group → service)
- **Config Versions**: Create, validate, and activate configuration versions with full version history
- **Config Resolver**: Resolve merged effective configurations across hierarchy
- **Audit Trail**: Complete audit log with filtering and export capabilities
- **Professional UI**: Material-UI based design with beautiful gradients and animations
- **Responsive**: Fully responsive design for desktop, tablet, and mobile

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm/yarn
- Backend API running at `http://localhost:8000/api/v1`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
src/
├── components/          # Reusable components
│   ├── Layout.tsx      # Main layout with sidebar and topbar
│   ├── TopBar.tsx      # Application header
│   ├── Sidebar.tsx     # Navigation menu
│   └── StatsCard.tsx   # Stats card component
├── pages/              # Page components
│   ├── Dashboard.tsx   # Dashboard page
│   ├── Schemas.tsx     # Schema management
│   ├── ConfigItems.tsx # Config items management
│   ├── ConfigVersions.tsx # Versions management
│   ├── ResolvedConfig.tsx # Config resolver
│   └── AuditTrail.tsx  # Audit log viewer
├── services/           # API services
│   └── api.ts         # API client with all endpoints
├── stores/             # State management with Zustand
│   └── app.ts         # Global application state
├── types/              # TypeScript type definitions
│   └── index.ts       # API response types
├── App.tsx            # Main app component with routing
├── main.tsx           # Application entry point
└── index.css          # Global styles with Tailwind CSS
```

## 🔌 API Integration

The frontend communicates with the ConfigSphere API through a centralized API client in `src/services/api.ts`.

### Endpoints Mapped

#### Schemas
- `GET /schemas/` - List all schemas
- `POST /schemas/` - Create schema
- `GET /schemas/{id}/` - Get schema by ID

#### Config Items
- `GET /config-items/` - List config items
- `POST /config-items/` - Create config item
- `GET /config-items/{id}/` - Get config item by ID

#### Config Versions
- `GET /config-items/{id}/versions/` - List versions for config item
- `POST /config-items/{id}/versions/` - Create new version
- `GET /config-versions/{id}/` - Get version by ID
- `POST /config-versions/{id}/activate/` - Activate a version

#### Resolved Config
- `GET /resolved-config/` - Get merged effective config with query params:
  - `?global=default`
  - `?region=us-west`
  - `?group=payment-team`
  - `?service=payment-service`

#### Audit Events
- `GET /audit-events/` - List audit events with optional filtering

## 🎯 Features by Page

### Dashboard
- Quick stats cards showing:
  - Total schemas
  - Total config items
  - Total audit events
  - Hierarchy levels information
- Recent activity feed with event type badges
- Quick action buttons to create new resources
- System information display

### Schemas
- View all schemas in a data table
- Create new schemas with JSON Schema definitions
- View schema definitions in a dialog
- Filter and search capabilities

### Config Items
- Manage configuration items across all hierarchy levels
- Scope level indicator with color coding
- Schema attachment support
- Scope details display (global/region/group/service names)
- Create items at any hierarchy level with proper field validation

### Config Versions
- View all versions across all config items
- Version status indication (DRAFT, VALIDATED, ACTIVE, ARCHIVED)
- Create new versions with payload and change summary
- Activate validated versions
- View full payload and checksum information

### Config Resolver
- Query config at any hierarchy level
- Interactive scope selector
- View merged effective configuration
- See which scope levels contributed to final config
- Display configuration layers with checksums
- Full payload viewer

### Audit Trail
- Timeline of all system events
- Filter by:
  - Event type
  - Actor (who made the change)
  - Date range
- Export audit log to CSV
- Event type badges with color coding
- Event statistics

## 🎨 Design Highlights

- **Color Scheme**: Indigo/Purple gradient theme with professional appearance
- **Typography**: Inter font family for clean, modern look
- **Components**: Material-UI for consistency and accessibility
- **Animations**: Smooth transitions and slide-in animations
- **Responsiveness**: Mobile-first design approach

## 🔧 Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:8000/api/v1
```

## 📦 Dependencies

### Core
- **react**: 18.2.0 - UI library
- **react-dom**: 18.2.0 - React DOM rendering
- **react-router-dom**: 6.21.0 - Client-side routing
- **vite**: 5.0.0 - Build tool

### State Management & API
- **zustand**: 4.4.0 - Lightweight state management
- **axios**: 1.6.0 - HTTP client

### UI & Styling
- **@mui/material**: 5.14.0 - Material Design components
- **@mui/icons-material**: 5.14.0 - Material Design icons
- **tailwindcss**: 3.4.0 - Utility-first CSS
- **@emotion/react**: 11.11.0 - CSS-in-JS for MUI

### Development
- **typescript**: 5.3.0 - Type safety
- **@types/react**: 18.2.0 - React type definitions

## 🚀 Deployment

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Docker Compose
Update the main docker-compose.yml to include the frontend service:

```yaml
services:
  web:
    # ... existing Django service
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://web:8000/api/v1
    depends_on:
      - web
```

## 🧪 Testing

Currently using manual testing through the UI. For automated testing:

```bash
# Add Jest and React Testing Library
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest
```

## 📝 Notes

- All API requests are logged to the browser console for debugging
- Error responses are properly handled and displayed to users
- The application automatically creates audit event entries for all state changes
- Checksums are generated server-side using SHA-256
- Type-safe API interactions with full TypeScript support

## 🤝 Contributing

When adding new pages:
1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add menu item in `src/components/Sidebar.tsx`
4. Use Layout component for consistent styling
5. Follow the existing TypeScript patterns

## 📄 License

Same as ConfigSphere backend project

## 🆘 Support

For issues or questions:
1. Check the backend API documentation
2. Review browser console for API errors
3. Verify backend is running and accessible
4. Check network tab in DevTools for request/response details
