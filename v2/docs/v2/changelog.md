# V2 Changelog

## 2026-04-11

- created V2 parallel architecture under `ConfigSphere/v2`
- added control-plane, delivery, and worker services
- added PostgreSQL and DynamoDB data model
- added governance, propagation, conflict, and rollback documentation
- added persistent local Docker volumes for PostgreSQL, Kafka, Zookeeper, and DynamoDB Local
- implemented bootstrap-first-admin and admin RBAC management APIs
- added RBAC audit persistence and admin-flow documentation
- switched revision authoring to local-override maps instead of full materialized configs
- updated request UI and diff rendering to show override-only changes while runtime delivery remains materialized
- added service-scoped delivery API keys for SDK and runtime polling clients
- added a separate realtime demo stack with dummy polling services and a dedicated dashboard
