# Config Tree

## Rules

- Each service owns one tree of config nodes.
- Path uniqueness is enforced per service.
- Maximum total nodes per service: `100`
- Maximum depth per service: `20`
- Maximum keys per materialized config: `1000`
- Maximum value size per key: `10000`

## Node creation

### Root

- Root is typically `/global`
- Root requires a base materialized config

### Child

- Child path is `parent.path + "/" + segment`
- Child copies the parent materialized config
- Child starts with empty `localOverrides`
- Child starts with empty `overrideKeys`

## Read behavior

- Runtime clients fetch only the active precomputed config for an exact path
- No inheritance is computed at read time
