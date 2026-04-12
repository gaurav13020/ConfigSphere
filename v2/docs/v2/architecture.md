# ConfigSphere V2 Architecture

ConfigSphere V2 uses a reduced service architecture:

- **Control Plane Service**
  - owns service tree metadata
  - owns governance workflow
  - owns RBAC enforcement
  - submits implement and rollback jobs
- **Delivery Service**
  - serves exact-path active config
  - exposes version polling endpoint
- **Worker Service**
  - consumes Kafka jobs
  - computes propagation
  - activates versions
  - executes rollback

Storage split:

- **PostgreSQL**
  - metadata
  - workflow
  - RBAC bindings
  - version pointers
  - jobs
- **DynamoDB Local**
  - active config payloads
  - proposed revision payloads
  - candidate payloads

Auth split:

- **Keycloak**
  - authentication and identity
- **Application DB**
  - service-scoped RBAC bindings

Read model:

- runtime clients fetch precomputed configs only
- no inheritance is computed at read time

Write model:

- proposals are stored as immutable revisions
- approved implementations are processed asynchronously
- worker writes candidate versions and atomically activates them
