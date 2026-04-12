# Service Boundaries

## Control Plane

Responsibilities:

- create services
- create root and child config nodes
- create change requests
- create revisions
- comments and reviews
- approve and implement commands
- rollback request creation and approval
- RBAC checks

Does not:

- serve runtime config to SDKs
- execute propagation directly inside request handlers

## Delivery

Responsibilities:

- fetch active config by exact path
- fetch current tree version for polling

Does not:

- handle governance workflow
- write config metadata
- compute inheritance

## Worker

Responsibilities:

- consume implement and rollback jobs
- propagate approved changes
- activate new versions
- mark request and rollback state
- emit or stub Jira sync events

Does not:

- serve end-user APIs
- own RBAC or reviewer decisions
