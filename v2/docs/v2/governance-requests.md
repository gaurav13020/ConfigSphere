# Governance Requests

## Request lifecycle

- `DRAFT`
- `SUBMITTED`
- `IN_REVIEW`
- `CHANGES_REQUESTED`
- `APPROVED`
- `REJECTED`
- `CONFLICTED`
- `IMPLEMENTING`
- `IMPLEMENTED`
- `FAILED`

## Revision rules

- Revisions are immutable
- Only the latest revision may be reviewed or implemented
- Creating a new revision resets prior approval semantics

## Storage

- PostgreSQL stores request and revision metadata
- DynamoDB stores the proposed full config document for each revision
