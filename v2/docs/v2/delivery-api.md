# Delivery API

## Endpoints

### `GET /v1/config`

Query parameters:

- `service`
- `path`

Returns:

- service metadata
- node metadata
- active version id
- current tree version
- `materializedConfig`

### `GET /v1/config/version`

Query parameters:

- `service`
- `path`

Returns:

- active `versionId`
- current service `treeVersion`

This endpoint is intended for SDK polling.
