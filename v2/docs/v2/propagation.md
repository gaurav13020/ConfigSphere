# Propagation

## Model

- Configs are fully materialized per node
- Inheritance is applied only during subconfig creation and propagation
- Each change request revision proposes only `localOverrides`
- Missing keys in `localOverrides` are inherited automatically from the parent
- Each node payload stores:
  - `materializedConfig`
  - `localOverrides`
  - `overrideKeys`

## Revision Authoring Flow

- A revision stores only the node's proposed `localOverrides`
- Control plane computes the effective `materializedConfig` as:
  - parent `materializedConfig`
  - plus proposed `localOverrides`
- Removing a key from the override map means the node inherits that key again
- The worker propagates only the resulting materialized changes to descendants that do not override those keys

## Implement flow

1. load approved revision
2. compare against current active payload
3. derive `localOverrides` and `overrideKeys` relative to parent
4. compute changed keys
5. create candidate version for target node
6. walk descendants breadth-first
7. update only keys that are not overridden in each child
8. create candidate versions for affected descendants
9. atomically activate all new version pointers

## Branch pruning

If a child overrides a key, propagation for that key stops at that branch root.

## Consistency

- runtime clients only see committed active versions
- worker writes candidate versions before activation
- activation updates node pointers and service tree version in one DB transaction
