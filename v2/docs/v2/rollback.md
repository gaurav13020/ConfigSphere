# Rollback

## Rules

- rollback is initiated from the UI
- rollback is represented as a new auditable change, not by reactivating old rows in place
- rollback uses a previous active node version as the source payload
- rollback propagates to descendants using the same inherited-key rules as normal implementation

## Flow

1. create rollback request
2. approve rollback request
3. implement rollback
4. worker creates a new active version derived from the target historical payload
5. descendants update only where keys are inherited
