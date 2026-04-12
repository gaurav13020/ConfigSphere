# ConfigSphere V2

ConfigSphere V2 is a new parallel implementation of the platform using:

- FastAPI
- PostgreSQL
- DynamoDB Local
- Kafka
- Keycloak
- Docker Compose

The V2 stack intentionally lives beside the current Django implementation and does
not modify or replace it.

## Services

- `control-plane`: config tree, governance workflow, RBAC checks, implement and rollback commands
- `delivery`: SDK-facing reads for precomputed active config
- `worker`: Kafka-driven propagation, rollback execution, and Jira sync stubs

## Local Development

```bash
cd ConfigSphere/v2
docker compose up --build
```

Service URLs:

- Control Plane: `http://localhost:8100`
- Delivery: `http://localhost:8101`
- Frontend: `http://localhost:3001` with `--profile ui`
- Keycloak: `http://localhost:8080`
- PostgreSQL: `localhost:5433`
- DynamoDB Local: `http://localhost:8002`

## Memory Tips

On a 16 GB laptop, avoid running both the old stack and V2 at the same time.

Recommended startup flow:

```bash
# backend services only
docker compose up --build

# add the UI only when you need it
docker compose --profile ui up --build
```

## Current Feature Coverage

Implemented in this initial V2 slice:

- platform foundation and compose stack
- shared SQLAlchemy data model
- service-scoped RBAC skeleton with Keycloak JWT validation and dev fallback
- service and config node creation
- active config payload storage in DynamoDB
- delivery read APIs for exact-path config and version polling
- config change request and revision workflow
- comments, review, approval, and implement command submission
- async job persistence and Kafka producer abstraction
- worker-side propagation and rollback processing primitives
- rollback request APIs
- documentation for the V2 architecture and implemented features

Deferred or intentionally lightweight in this slice:

- full Jira REST integration
- production-grade Keycloak realm bootstrap
- UI implementation
- full SDK refresh against the new delivery service
- auto-merge conflict handling
